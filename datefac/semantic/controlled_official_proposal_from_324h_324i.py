from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

import pandas as pd


EXPECTED_324H_DECISION = "OFFICIAL_RULE_CANDIDATE_FROM_324G_324H_READY_FOR_CONTROLLED_PROPOSAL"
EXPECTED_324G_READY_WARN_DECISION = "SCOPE_NOISE_HUMAN_CONFIRMED_SANDBOX_REPLAY_324G_READY_WITH_WARNINGS"
EXPECTED_324G_READY_DECISION = (
    "SCOPE_NOISE_HUMAN_CONFIRMED_SANDBOX_REPLAY_324G_READY_FOR_324H_OFFICIAL_RULE_CANDIDATE"
)
READY_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_FROM_324H_324I_READY_FOR_324J_DRY_RUN"
READY_WARN_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_FROM_324H_324I_READY_WITH_WARNINGS"
NOT_READY_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_FROM_324H_324I_NOT_READY"

ALLOWED_324G_WARN_CHECK = "reference_323n::historical_duplicates_unchanged_only"
ALLOWED_CARRIED_WARNING = "historical_duplicates_unchanged_only:new_duplicate_delta_count=0"

OFFICIAL_ALIAS_ASSET_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")
FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")


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


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = _norm(value).lower()
    return text in {"1", "true", "yes", "y"}


def _safe_numeric_sum(df: pd.DataFrame, column: str) -> int:
    if df.empty or column not in df.columns:
        return 0
    return int(pd.to_numeric(df[column], errors="coerce").fillna(0).sum())


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _dedupe_preserve(items: Iterable[Any]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for item in items:
        clean = _norm(item)
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _join_unique(items: Iterable[Any], limit: int = 16) -> str:
    return " | ".join(_dedupe_preserve(items)[:limit])


def _split_pipe(value: Any) -> List[str]:
    text = _norm(value)
    if not text:
        return []
    return [item.strip() for item in text.split("|") if item.strip()]


def _load_scope_reference() -> Tuple[bool, Dict[str, Any], pd.DataFrame]:
    payload = _read_json(FORMAL_SCOPE_RULES_PATH)
    rules = payload.get("rules", {}) if isinstance(payload, dict) else {}
    rows: List[Dict[str, Any]] = []
    if isinstance(rules, dict):
        for rule_id, item in rules.items():
            if not isinstance(item, dict):
                continue
            rows.append(
                {
                    "rule_id": _norm(item.get("rule_id")) or _norm(rule_id),
                    "normalized_label": _norm(item.get("normalized_label")),
                    "normalized_label_key": _normalize_label(item.get("normalized_label")),
                    "target_group": _norm(item.get("target_group")),
                    "scope_action": _norm(item.get("scope_action")),
                    "rule_type": _norm(item.get("rule_type")),
                    "promotion_status": _norm(item.get("promotion_status")),
                    "source_rule_candidate_id": _norm(item.get("source_rule_candidate_id")),
                }
            )
    return bool(payload), payload, pd.DataFrame(rows).fillna("")


def _load_alias_reference() -> Tuple[bool, Dict[str, Any], pd.DataFrame]:
    payload = _read_json(OFFICIAL_ALIAS_ASSET_PATH)
    groups = payload.get("groups", {}) if isinstance(payload, dict) else {}
    rows: List[Dict[str, Any]] = []
    if isinstance(groups, dict):
        for group_name, entries in groups.items():
            if not isinstance(entries, list):
                continue
            for item in entries:
                if not isinstance(item, dict):
                    continue
                rows.append(
                    {
                        "group_name": _norm(group_name),
                        "normalized_label": _norm(item.get("normalized_label")),
                        "normalized_label_key": _normalize_label(item.get("normalized_label")),
                        "metric_code": _norm(item.get("metric_code")),
                        "metric_family": _norm(item.get("metric_family")) or _norm(group_name),
                        "rule_id": _norm(item.get("rule_id")),
                    }
                )
    return bool(payload), payload, pd.DataFrame(rows).fillna("")


def load_controlled_official_proposal_from_324h_inputs(
    official_rule_candidate_dir: Path,
    sandbox_replay_dir: Path,
) -> Dict[str, Any]:
    package_json = _read_json(
        official_rule_candidate_dir
        / "official_rule_candidate_from_324g_324h_candidate_package.json"
    )
    return {
        "official_rule_candidate_summary": _read_json(
            official_rule_candidate_dir
            / "official_rule_candidate_from_324g_324h_summary.json"
        ),
        "official_rule_candidate_qa": _read_json(
            official_rule_candidate_dir / "official_rule_candidate_from_324g_324h_qa.json"
        ),
        "effective_candidates_df": pd.DataFrame(
            package_json.get("effective_unique_candidates", [])
            if isinstance(package_json.get("effective_unique_candidates", []), list)
            else []
        ).fillna(""),
        "scope_candidates_df": pd.DataFrame(
            package_json.get("scope_candidates", [])
            if isinstance(package_json.get("scope_candidates", []), list)
            else []
        ).fillna(""),
        "candidate_source_bridge_df": pd.DataFrame(
            package_json.get("candidate_source_bridge", [])
            if isinstance(package_json.get("candidate_source_bridge", []), list)
            else []
        ).fillna(""),
        "source_provenance_df": pd.DataFrame(
            package_json.get("source_provenance", [])
            if isinstance(package_json.get("source_provenance", []), list)
            else []
        ).fillna(""),
        "sandbox_summary": _read_json(
            sandbox_replay_dir / "scope_noise_human_confirmed_sandbox_replay_324g_summary.json"
        ),
        "sandbox_qa": _read_json(
            sandbox_replay_dir / "scope_noise_human_confirmed_sandbox_replay_324g_qa.json"
        ),
    }


def _qa_allowed_324g_warning(sandbox_qa: Dict[str, Any]) -> bool:
    checks = sandbox_qa.get("checks", [])
    if not isinstance(checks, list):
        return False
    warn_checks = [
        _norm(item.get("check_name"))
        for item in checks
        if isinstance(item, dict) and _norm(item.get("status")) == "WARN"
    ]
    return bool(warn_checks) and set(warn_checks) == {ALLOWED_324G_WARN_CHECK}


def _historical_duplicate_warning_confirmed(sandbox_qa: Dict[str, Any]) -> bool:
    for item in sandbox_qa.get("checks", []):
        if (
            isinstance(item, dict)
            and _norm(item.get("check_name")) == ALLOWED_324G_WARN_CHECK
            and "new_duplicate_delta_count=0" in _norm(item.get("detail"))
        ):
            return True
    return False


def _target_plan_for_scope_candidate(
    candidate_row: Dict[str, Any],
    scope_reference_df: pd.DataFrame,
    alias_reference_df: pd.DataFrame,
) -> Dict[str, Any]:
    normalized_label_key = _normalize_label(candidate_row.get("normalized_label"))
    scope_rows = (
        scope_reference_df.loc[
            scope_reference_df["normalized_label_key"].astype(str) == normalized_label_key
        ].copy()
        if not scope_reference_df.empty
        else pd.DataFrame()
    )
    alias_rows = (
        alias_reference_df.loc[
            alias_reference_df["normalized_label_key"].astype(str) == normalized_label_key
        ].copy()
        if not alias_reference_df.empty
        else pd.DataFrame()
    )

    target_group_exists = (
        not scope_reference_df.empty
        and scope_reference_df["target_group"]
        .astype(str)
        .eq("core_metric_scope_exclusions")
        .any()
    )
    already_official_overlap = not scope_rows.empty
    alias_conflict = not alias_rows.empty

    overlap_status = "NO_OFFICIAL_OVERLAP"
    if already_official_overlap:
        existing_actions = _dedupe_preserve(scope_rows["scope_action"].tolist())
        if _norm(candidate_row.get("proposed_scope_action")) in existing_actions:
            overlap_status = "ALREADY_OFFICIAL_SAME_SCOPE_RULE"
        else:
            overlap_status = "ALREADY_OFFICIAL_DIFFERENT_SCOPE_RULE"

    target_conflict_status = "NO_TARGET_CONFLICT"
    if alias_conflict:
        target_conflict_status = "TARGET_CONFLICT_ALIAS_LABEL_ALREADY_USED"
    elif overlap_status == "ALREADY_OFFICIAL_DIFFERENT_SCOPE_RULE":
        target_conflict_status = "TARGET_CONFLICT_EXISTING_SCOPE_RULE"

    return {
        "target_asset_path": str(FORMAL_SCOPE_RULES_PATH),
        "target_rule_family": "formal_scope_rules",
        "target_asset_exists": FORMAL_SCOPE_RULES_PATH.exists(),
        "target_group_name": "core_metric_scope_exclusions",
        "target_group_exists_or_virtual": target_group_exists,
        "target_group_resolution": "EXISTING_GROUP" if target_group_exists else "MISSING_GROUP",
        "future_operation_type": "APPEND_SCOPE_EXCLUSION_RULE",
        "target_official_rule_category": "official_scope_rule_candidate",
        "intended_future_target_file_or_rule_group": (
            "data/mapping/formal_scope_rules.json::core_metric_scope_exclusions"
        ),
        "already_official_overlap_status": overlap_status,
        "target_conflict_status": target_conflict_status,
        "existing_scope_rule_ids": _join_unique(scope_rows["rule_id"].tolist(), limit=8),
        "existing_alias_rule_ids": _join_unique(alias_rows["rule_id"].tolist(), limit=8),
        "alias_conflict": alias_conflict,
    }


def build_controlled_official_proposal_from_324h(
    official_rule_candidate_summary: Dict[str, Any],
    official_rule_candidate_qa: Dict[str, Any],
    effective_candidates_df: pd.DataFrame,
    scope_candidates_df: pd.DataFrame,
    candidate_source_bridge_df: pd.DataFrame,
    source_provenance_df: pd.DataFrame,
    sandbox_summary: Dict[str, Any],
    sandbox_qa: Dict[str, Any],
    alias_reference_loaded: bool,
    alias_reference_df: pd.DataFrame,
    scope_reference_loaded: bool,
    scope_reference_df: pd.DataFrame,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa(
        "readiness::324h_decision",
        "PASS"
        if _norm(official_rule_candidate_summary.get("decision")) == EXPECTED_324H_DECISION
        else "FAIL",
        _norm(official_rule_candidate_summary.get("decision")),
    )
    add_qa(
        "readiness::324h_qa_fail_count",
        "PASS" if _safe_int(official_rule_candidate_summary.get("qa_fail_count")) == 0 else "FAIL",
        str(official_rule_candidate_summary.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::324h_qa_json_fail_count",
        "PASS" if _safe_int(official_rule_candidate_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(official_rule_candidate_qa.get("qa_fail_count", "")),
    )
    for key, expected in [
        ("source_sandbox_rule_count", 1),
        ("candidate_count", 1),
        ("scope_candidate_count", 1),
        ("ready_for_controlled_proposal_count", 1),
        ("needs_review_candidate_count", 0),
        ("rejected_candidate_count", 0),
        ("affected_candidate_count", 42),
        ("expected_trusted_gain", 0),
        ("expected_review_reduction", 42),
        ("expected_out_of_scope_or_rejected_gain", 42),
        ("duplicate_candidate_id_count", 0),
        ("already_official_overlap_count", 0),
        ("alias_conflict_count", 0),
        ("conflict_count", 0),
    ]:
        add_qa(
            f"readiness::324h_{key}",
            "PASS" if _safe_int(official_rule_candidate_summary.get(key)) == expected else "FAIL",
            f"expected={expected} actual={official_rule_candidate_summary.get(key, '')}",
        )

    sandbox_decision = _norm(sandbox_summary.get("decision"))
    sandbox_warn_count = _safe_int(sandbox_summary.get("qa_warn_count"))
    add_qa(
        "readiness::324g_decision_allowed",
        "PASS"
        if sandbox_decision == EXPECTED_324G_READY_DECISION
        or (
            sandbox_decision == EXPECTED_324G_READY_WARN_DECISION
            and sandbox_warn_count > 0
            and _qa_allowed_324g_warning(sandbox_qa)
        )
        else "FAIL",
        sandbox_decision,
    )
    add_qa(
        "readiness::324g_qa_fail_count",
        "PASS" if _safe_int(sandbox_summary.get("qa_fail_count")) == 0 else "FAIL",
        str(sandbox_summary.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::324g_core_false_exclusion_count",
        "PASS" if _safe_int(sandbox_summary.get("core_false_exclusion_count")) == 0 else "FAIL",
        str(sandbox_summary.get("core_false_exclusion_count", "")),
    )
    add_qa(
        "readiness::324g_conflict_count",
        "PASS" if _safe_int(sandbox_summary.get("conflict_count")) == 0 else "FAIL",
        str(sandbox_summary.get("conflict_count", "")),
    )

    carried_warnings = _dedupe_preserve(official_rule_candidate_summary.get("carried_warnings", []))
    allowed_carried_warnings_only = not carried_warnings or set(carried_warnings) == {
        ALLOWED_CARRIED_WARNING
    }
    add_qa(
        "warnings::carried_warning_allowed_only",
        "PASS" if allowed_carried_warnings_only else "FAIL",
        " | ".join(carried_warnings),
    )
    if carried_warnings:
        add_qa(
            "warnings::historical_duplicates_unchanged_only",
            "WARN" if _historical_duplicate_warning_confirmed(sandbox_qa) else "FAIL",
            ALLOWED_CARRIED_WARNING,
        )

    ready_candidates_df = (
        effective_candidates_df.loc[
            effective_candidates_df["rule_candidate_status"].astype(str)
            == "READY_FOR_CONTROLLED_PROPOSAL"
        ]
        .copy()
        .sort_values(["normalized_label_key"], ascending=[True])
        .reset_index(drop=True)
        if not effective_candidates_df.empty
        else pd.DataFrame()
    )
    add_qa(
        "inputs::loaded_ready_candidate_count",
        "PASS" if len(ready_candidates_df) == 1 else "FAIL",
        f"actual={len(ready_candidates_df)}",
    )
    add_qa(
        "inputs::loaded_ready_scope_candidate_count",
        "PASS"
        if len(ready_candidates_df) == 1
        and ready_candidates_df["candidate_type"].astype(str).eq("scope_noise").all()
        else "FAIL",
        f"actual={int(ready_candidates_df['candidate_type'].astype(str).eq('scope_noise').sum()) if not ready_candidates_df.empty else 0}",
    )
    add_qa(
        "inputs::loaded_ready_alias_candidate_count",
        "PASS"
        if ready_candidates_df.empty
        or int(ready_candidates_df["candidate_type"].astype(str).eq("alias").sum()) == 0
        else "FAIL",
        f"actual={int(ready_candidates_df['candidate_type'].astype(str).eq('alias').sum()) if not ready_candidates_df.empty else 0}",
    )

    proposal_rows: List[Dict[str, Any]] = []
    target_plan_rows: List[Dict[str, Any]] = []
    bridge_rows: List[Dict[str, Any]] = []
    provenance_rows: List[Dict[str, Any]] = []

    for index, (_, candidate_row) in enumerate(ready_candidates_df.iterrows(), start=1):
        row_dict = candidate_row.to_dict()
        bridge_df = (
            candidate_source_bridge_df.loc[
                candidate_source_bridge_df["rule_candidate_id"].astype(str)
                == _norm(row_dict.get("rule_candidate_id"))
            ]
            .copy()
            .reset_index(drop=True)
            if not candidate_source_bridge_df.empty
            else pd.DataFrame()
        )
        provenance_df = (
            source_provenance_df.loc[
                source_provenance_df["source_rule_id"]
                .astype(str)
                .isin(_split_pipe(row_dict.get("source_rule_ids")))
            ]
            .copy()
            .reset_index(drop=True)
            if not source_provenance_df.empty
            else pd.DataFrame()
        )
        target_plan = _target_plan_for_scope_candidate(
            candidate_row=row_dict,
            scope_reference_df=scope_reference_df,
            alias_reference_df=alias_reference_df,
        )

        missing_provenance_fields = [
            _norm(row_dict.get("source_candidate_ids_324a")),
            _norm(row_dict.get("source_review_ids_324b")),
            _norm(row_dict.get("source_request_ids")),
            _norm(row_dict.get("source_response_ids_324d")),
            _norm(row_dict.get("source_validation_ids_324e")),
            _norm(row_dict.get("source_confirmation_ids")),
            _norm(row_dict.get("source_sandbox_rule_ids_324g")),
            _norm(row_dict.get("rule_candidate_id")),
        ]
        missing_provenance = any(not item for item in missing_provenance_fields) or provenance_df.empty
        missing_target_asset_or_group = (
            not _safe_bool(target_plan.get("target_asset_exists"))
            or not _safe_bool(target_plan.get("target_group_exists_or_virtual"))
        )
        already_official_overlap = _norm(target_plan.get("already_official_overlap_status")).startswith(
            "ALREADY_OFFICIAL"
        )
        target_conflict = _norm(target_plan.get("target_conflict_status")).startswith(
            "TARGET_CONFLICT"
        )

        proposal_status = (
            "REJECTED"
            if target_conflict
            else "NEEDS_REVIEW"
            if already_official_overlap or missing_target_asset_or_group or missing_provenance
            else "READY_FOR_DRY_RUN"
        )
        proposal_id = f"proposal_324i::scope::{index:03d}"

        proposal_row = {
            "controlled_proposal_id": proposal_id,
            "source_rule_candidate_id_324h": _norm(row_dict.get("rule_candidate_id")),
            "candidate_type": "scope_noise",
            "proposal_type": _norm(row_dict.get("proposal_type")) or "out_of_scope",
            "proposal_status": proposal_status,
            "normalized_label": _norm(row_dict.get("normalized_label")),
            "normalized_label_key": _norm(row_dict.get("normalized_label_key")),
            "proposed_scope_action": _norm(row_dict.get("proposed_scope_action")),
            "target_asset_path": _norm(target_plan.get("target_asset_path")),
            "target_rule_family": _norm(target_plan.get("target_rule_family")),
            "target_group_name": _norm(target_plan.get("target_group_name")),
            "target_group_resolution": _norm(target_plan.get("target_group_resolution")),
            "future_operation_type": _norm(target_plan.get("future_operation_type")),
            "target_official_rule_category": _norm(
                target_plan.get("target_official_rule_category")
            ),
            "intended_future_target_file_or_rule_group": _norm(
                target_plan.get("intended_future_target_file_or_rule_group")
            ),
            "target_asset_exists": _safe_bool(target_plan.get("target_asset_exists")),
            "target_group_exists_or_virtual": _safe_bool(
                target_plan.get("target_group_exists_or_virtual")
            ),
            "already_official_overlap_status": _norm(
                target_plan.get("already_official_overlap_status")
            ),
            "target_conflict_status": _norm(target_plan.get("target_conflict_status")),
            "alias_conflict": _safe_bool(target_plan.get("alias_conflict")),
            "existing_scope_rule_ids": _norm(target_plan.get("existing_scope_rule_ids")),
            "existing_alias_rule_ids": _norm(target_plan.get("existing_alias_rule_ids")),
            "source_rule_count": _safe_int(row_dict.get("source_rule_count")),
            "duplicate_source_rule": _safe_bool(row_dict.get("duplicate_source_rule")),
            "dedupe_resolution": _norm(row_dict.get("dedupe_resolution")),
            "duplicate_provenance_retained_only": True,
            "source_rule_ids": _norm(row_dict.get("source_rule_ids")),
            "source_candidate_ids_324a": _norm(row_dict.get("source_candidate_ids_324a")),
            "source_review_ids_324b": _norm(row_dict.get("source_review_ids_324b")),
            "source_request_ids_324c": _norm(row_dict.get("source_request_ids")),
            "source_response_ids_324d": _norm(row_dict.get("source_response_ids_324d")),
            "source_validation_ids_324e": _norm(row_dict.get("source_validation_ids_324e")),
            "source_confirmation_ids_324f": _norm(row_dict.get("source_confirmation_ids")),
            "source_sandbox_rule_ids_324g": _norm(
                row_dict.get("source_sandbox_rule_ids_324g")
            ),
            "expected_affected_candidate_count": _safe_int(
                row_dict.get("actual_affected_candidate_count")
                or row_dict.get("expected_affected_candidate_count")
            ),
            "expected_trusted_gain": _safe_int(row_dict.get("expected_trusted_gain")),
            "expected_review_reduction": _safe_int(
                row_dict.get("expected_review_reduction")
            ),
            "expected_out_of_scope_or_rejected_gain": _safe_int(
                row_dict.get("expected_out_of_scope_or_rejected_gain")
            ),
            "priority_score_max": row_dict.get("priority_score_max"),
            "risk_flags": _norm(row_dict.get("risk_flags")),
            "reviewer_names": _norm(row_dict.get("reviewer_names")),
            "reviewer_notes": _norm(row_dict.get("reviewer_notes")),
            "review_timestamps": _norm(row_dict.get("review_timestamps")),
            "sample_table_titles": _norm(row_dict.get("sample_table_titles")),
            "sample_texts": _norm(row_dict.get("sample_texts")),
            "sample_years": _norm(row_dict.get("sample_years")),
            "provenance_text_samples": _norm(row_dict.get("provenance_text_samples")),
            "candidate_readiness_reason": _norm(row_dict.get("candidate_readiness_reason")),
            "rollback_note": (
                f"Before any future dry run/application stage, remove controlled proposal "
                f"'{proposal_id}' for label '{_norm(row_dict.get('normalized_label'))}' "
                "from the 324I proposal package."
            ),
            "eligible_for_324j_dry_run": proposal_status == "READY_FOR_DRY_RUN",
            "proposal_only_no_apply_confirmed": True,
        }
        proposal_rows.append(proposal_row)

        target_plan_rows.append(
            {
                "controlled_proposal_id": proposal_id,
                "candidate_type": "scope_noise",
                "normalized_label": proposal_row["normalized_label"],
                "target_asset_path": proposal_row["target_asset_path"],
                "target_rule_family": proposal_row["target_rule_family"],
                "target_group_name": proposal_row["target_group_name"],
                "target_group_resolution": proposal_row["target_group_resolution"],
                "future_operation_type": proposal_row["future_operation_type"],
                "target_official_rule_category": proposal_row[
                    "target_official_rule_category"
                ],
                "already_official_overlap_status": proposal_row[
                    "already_official_overlap_status"
                ],
                "target_conflict_status": proposal_row["target_conflict_status"],
                "eligible_for_324j_dry_run": proposal_row["eligible_for_324j_dry_run"],
            }
        )

        for _, bridge_row in bridge_df.iterrows():
            bridge_rows.append(
                {
                    "controlled_proposal_id": proposal_id,
                    "source_rule_candidate_id_324h": _norm(row_dict.get("rule_candidate_id")),
                    "source_rule_id_324g": _norm(bridge_row.get("source_rule_id")),
                    "source_candidate_id_324a": _norm(
                        bridge_row.get("source_refined_scope_candidate_id")
                    ),
                    "source_review_id_324b": _norm(bridge_row.get("source_scope_review_id")),
                    "source_request_id_324c": _norm(bridge_row.get("request_id")),
                    "source_response_id_324d": _norm(bridge_row.get("response_id_324d")),
                    "source_validation_id_324e": _norm(bridge_row.get("validation_id_324e")),
                    "source_confirmation_id_324f": _norm(bridge_row.get("confirmation_id")),
                    "source_rule_actual_affected_candidate_count": _safe_int(
                        bridge_row.get("source_rule_actual_affected_candidate_count")
                    ),
                    "source_rule_trusted_gain": _safe_int(
                        bridge_row.get("source_rule_trusted_gain")
                    ),
                    "source_rule_review_reduction": _safe_int(
                        bridge_row.get("source_rule_review_reduction")
                    ),
                    "source_rule_out_of_scope_or_rejected_gain": _safe_int(
                        bridge_row.get("source_rule_out_of_scope_or_rejected_gain")
                    ),
                    "reviewer_name": _norm(bridge_row.get("reviewer_name")),
                    "review_timestamp": _norm(bridge_row.get("review_timestamp")),
                    "provenance_text": _norm(bridge_row.get("provenance_text")),
                }
            )

        for _, prov_row in provenance_df.iterrows():
            provenance_rows.append(
                {
                    "controlled_proposal_id": proposal_id,
                    "source_rule_id_324g": _norm(prov_row.get("source_rule_id")),
                    "source_candidate_id_324a": _norm(prov_row.get("candidate_id_324a")),
                    "source_review_id_324b": _norm(prov_row.get("review_id_324b")),
                    "source_request_id_324c": _norm(prov_row.get("request_id")),
                    "source_response_id_324d": _norm(prov_row.get("response_id_324d")),
                    "source_validation_id_324e": _norm(prov_row.get("validation_id_324e")),
                    "source_confirmation_id_324f": _norm(
                        prov_row.get("confirmation_id_324f")
                    ),
                    "source_sandbox_rule_id_324g": _norm(
                        prov_row.get("sandbox_rule_id_324g")
                    ),
                    "sample_candidate_ids": _norm(prov_row.get("sample_candidate_ids")),
                    "sample_table_titles": _norm(prov_row.get("sample_table_titles")),
                    "sample_texts": _norm(prov_row.get("sample_texts")),
                    "sample_years": _norm(prov_row.get("sample_years")),
                    "sample_evidence_text": _norm(prov_row.get("sample_evidence_text")),
                    "risk_flags": _norm(prov_row.get("risk_flags")),
                    "provenance_text": _norm(prov_row.get("provenance_text")),
                    "source_group_ids": _norm(prov_row.get("source_group_ids")),
                    "representative_group_id": _norm(
                        prov_row.get("representative_group_id")
                    ),
                    "source_stage_signatures": _norm(
                        prov_row.get("source_stage_signatures")
                    ),
                }
            )

    proposal_overview_df = pd.DataFrame(proposal_rows).fillna("")
    alias_proposals_df = pd.DataFrame(columns=proposal_overview_df.columns).fillna("")
    scope_proposals_df = (
        proposal_overview_df.loc[
            proposal_overview_df["candidate_type"].astype(str) == "scope_noise"
        ].copy()
        if not proposal_overview_df.empty
        else pd.DataFrame()
    )
    target_asset_plan_df = pd.DataFrame(target_plan_rows).fillna("")
    proposal_source_bridge_df = pd.DataFrame(bridge_rows).fillna("")
    provenance_samples_df = pd.DataFrame(provenance_rows).fillna("")

    duplicate_proposal_id_count = (
        int(proposal_overview_df["controlled_proposal_id"].astype(str).duplicated().sum())
        if not proposal_overview_df.empty
        else 0
    )
    already_official_overlap_count = (
        int(
            proposal_overview_df["already_official_overlap_status"]
            .astype(str)
            .str.startswith("ALREADY_OFFICIAL")
            .sum()
        )
        if not proposal_overview_df.empty
        else 0
    )
    alias_conflict_count = (
        int(proposal_overview_df["alias_conflict"].astype(bool).sum())
        if not proposal_overview_df.empty
        else 0
    )
    target_conflict_count = (
        int(
            proposal_overview_df["target_conflict_status"]
            .astype(str)
            .str.startswith("TARGET_CONFLICT")
            .sum()
        )
        if not proposal_overview_df.empty
        else 0
    )
    missing_target_asset_or_group_count = (
        int(
            (
                ~proposal_overview_df["target_asset_exists"].astype(bool)
                | ~proposal_overview_df["target_group_exists_or_virtual"].astype(bool)
            ).sum()
        )
        if not proposal_overview_df.empty
        else 0
    )
    missing_provenance_count = (
        int(
            proposal_overview_df[
                proposal_overview_df["source_candidate_ids_324a"].astype(str).eq("")
                | proposal_overview_df["source_review_ids_324b"].astype(str).eq("")
                | proposal_overview_df["source_request_ids_324c"].astype(str).eq("")
                | proposal_overview_df["source_response_ids_324d"].astype(str).eq("")
                | proposal_overview_df["source_validation_ids_324e"].astype(str).eq("")
                | proposal_overview_df["source_confirmation_ids_324f"].astype(str).eq("")
                | proposal_overview_df["source_sandbox_rule_ids_324g"].astype(str).eq("")
                | proposal_overview_df["source_rule_candidate_id_324h"].astype(str).eq("")
            ].shape[0]
        )
        if not proposal_overview_df.empty
        else 0
    )
    ready_proposal_count = (
        int(proposal_overview_df["proposal_status"].astype(str).eq("READY_FOR_DRY_RUN").sum())
        if not proposal_overview_df.empty
        else 0
    )
    review_proposal_count = (
        int(proposal_overview_df["proposal_status"].astype(str).eq("NEEDS_REVIEW").sum())
        if not proposal_overview_df.empty
        else 0
    )
    rejected_proposal_count = (
        int(proposal_overview_df["proposal_status"].astype(str).eq("REJECTED").sum())
        if not proposal_overview_df.empty
        else 0
    )

    add_qa(
        "proposal_counts::total",
        "PASS" if len(proposal_overview_df) == 1 else "FAIL",
        f"actual={len(proposal_overview_df)}",
    )
    add_qa(
        "proposal_counts::scope",
        "PASS" if len(scope_proposals_df) == 1 else "FAIL",
        f"actual={len(scope_proposals_df)}",
    )
    add_qa(
        "proposal_counts::alias",
        "PASS" if len(alias_proposals_df) == 0 else "FAIL",
        f"actual={len(alias_proposals_df)}",
    )
    add_qa(
        "proposal_counts::ready",
        "PASS" if ready_proposal_count == 1 else "FAIL",
        f"actual={ready_proposal_count}",
    )
    add_qa(
        "proposal_counts::needs_review",
        "PASS" if review_proposal_count == 0 else "FAIL",
        f"actual={review_proposal_count}",
    )
    add_qa(
        "proposal_counts::rejected",
        "PASS" if rejected_proposal_count == 0 else "FAIL",
        f"actual={rejected_proposal_count}",
    )
    add_qa(
        "target_plan::duplicate_proposal_id_count",
        "PASS" if duplicate_proposal_id_count == 0 else "FAIL",
        f"actual={duplicate_proposal_id_count}",
    )
    add_qa(
        "target_plan::already_official_overlap_count",
        "PASS" if already_official_overlap_count == 0 else "FAIL",
        f"actual={already_official_overlap_count}",
    )
    add_qa(
        "target_plan::alias_conflict_count",
        "PASS" if alias_conflict_count == 0 else "FAIL",
        f"actual={alias_conflict_count}",
    )
    add_qa(
        "target_plan::target_conflict_count",
        "PASS" if target_conflict_count == 0 else "FAIL",
        f"actual={target_conflict_count}",
    )
    add_qa(
        "target_plan::missing_target_asset_or_group_count",
        "PASS" if missing_target_asset_or_group_count == 0 else "FAIL",
        f"actual={missing_target_asset_or_group_count}",
    )
    add_qa(
        "provenance::missing_provenance_count",
        "PASS" if missing_provenance_count == 0 else "FAIL",
        f"actual={missing_provenance_count}",
    )
    add_qa(
        "provenance::source_bridge_row_count",
        "PASS" if len(proposal_source_bridge_df) == 1 else "FAIL",
        f"actual={len(proposal_source_bridge_df)}",
    )
    add_qa(
        "provenance::source_provenance_row_count",
        "PASS" if len(provenance_samples_df) == 1 else "FAIL",
        f"actual={len(provenance_samples_df)}",
    )

    expected_affected_candidate_count = _safe_numeric_sum(
        proposal_overview_df, "expected_affected_candidate_count"
    )
    expected_trusted_gain = _safe_numeric_sum(
        proposal_overview_df, "expected_trusted_gain"
    )
    expected_review_reduction = _safe_numeric_sum(
        proposal_overview_df, "expected_review_reduction"
    )
    expected_out_of_scope_or_rejected_gain = _safe_numeric_sum(
        proposal_overview_df, "expected_out_of_scope_or_rejected_gain"
    )
    add_qa(
        "impact::expected_affected_candidate_count",
        "PASS" if expected_affected_candidate_count == 42 else "FAIL",
        f"actual={expected_affected_candidate_count}",
    )
    add_qa(
        "impact::expected_trusted_gain",
        "PASS" if expected_trusted_gain == 0 else "FAIL",
        f"actual={expected_trusted_gain}",
    )
    add_qa(
        "impact::expected_review_reduction",
        "PASS" if expected_review_reduction == 42 else "FAIL",
        f"actual={expected_review_reduction}",
    )
    add_qa(
        "impact::expected_out_of_scope_or_rejected_gain",
        "PASS" if expected_out_of_scope_or_rejected_gain == 42 else "FAIL",
        f"actual={expected_out_of_scope_or_rejected_gain}",
    )

    add_qa(
        "safety::scope_reference_loaded",
        "PASS" if scope_reference_loaded else "FAIL",
        str(FORMAL_SCOPE_RULES_PATH),
    )
    add_qa(
        "safety::alias_reference_loaded",
        "PASS" if alias_reference_loaded else "FAIL",
        str(OFFICIAL_ALIAS_ASSET_PATH),
    )
    add_qa(
        "safety::proposal_only_no_apply_confirmed",
        "PASS",
        "324I creates a controlled proposal package only and does not apply semantic rules.",
    )
    add_qa(
        "safety::no_llm_or_api_call_executed",
        "PASS",
        "324I uses 324H outputs and cached 324G evidence only.",
    )

    qa_checks_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_checks_df["status"] == "PASS").sum()) if not qa_checks_df.empty else 0
    qa_warn_count = int((qa_checks_df["status"] == "WARN").sum()) if not qa_checks_df.empty else 0
    qa_fail_count = int((qa_checks_df["status"] == "FAIL").sum()) if not qa_checks_df.empty else 0
    blocking_reasons = (
        qa_checks_df.loc[qa_checks_df["status"] == "FAIL", "check_name"]
        .astype(str)
        .tolist()
        if not qa_checks_df.empty
        else []
    )

    summary = {
        "stage": "324I",
        "output_dir": "",
        "loaded_ready_candidate_count": int(len(ready_candidates_df)),
        "proposal_count": int(len(proposal_overview_df)),
        "alias_proposal_count": int(len(alias_proposals_df)),
        "scope_proposal_count": int(len(scope_proposals_df)),
        "ready_for_dry_run_proposal_count": ready_proposal_count,
        "needs_review_proposal_count": review_proposal_count,
        "rejected_proposal_count": rejected_proposal_count,
        "target_asset_plan_count": int(len(target_asset_plan_df)),
        "target_asset_file_count": int(
            len(_dedupe_preserve(target_asset_plan_df["target_asset_path"].tolist()))
        )
        if not target_asset_plan_df.empty
        else 0,
        "duplicate_proposal_id_count": duplicate_proposal_id_count,
        "already_official_overlap_count": already_official_overlap_count,
        "alias_conflict_count": alias_conflict_count,
        "target_conflict_count": target_conflict_count,
        "missing_target_asset_or_group_count": missing_target_asset_or_group_count,
        "missing_provenance_count": missing_provenance_count,
        "expected_affected_candidate_count": expected_affected_candidate_count,
        "expected_trusted_gain": expected_trusted_gain,
        "expected_review_reduction": expected_review_reduction,
        "expected_out_of_scope_or_rejected_gain": expected_out_of_scope_or_rejected_gain,
        "carried_warnings": carried_warnings,
        "proposal_only_no_apply_confirmed": True,
        "official_assets_not_modified_confirmed": True,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": (
            NOT_READY_DECISION
            if qa_fail_count > 0
            else READY_WARN_DECISION
            if qa_warn_count > 0
            else READY_DECISION
        ),
    }

    proposal_package_json = {
        "stage": "324I",
        "decision": summary["decision"],
        "source_readiness_summary": {
            "official_rule_candidate_decision": _norm(
                official_rule_candidate_summary.get("decision")
            ),
            "sandbox_replay_decision": sandbox_decision,
            "loaded_ready_candidate_count": summary["loaded_ready_candidate_count"],
        },
        "controlled_proposals": proposal_overview_df.to_dict(orient="records"),
        "alias_proposals": alias_proposals_df.to_dict(orient="records"),
        "scope_proposals": scope_proposals_df.to_dict(orient="records"),
        "target_asset_plan": target_asset_plan_df.to_dict(orient="records"),
        "proposal_source_bridge": proposal_source_bridge_df.to_dict(orient="records"),
        "provenance_samples": provenance_samples_df.to_dict(orient="records"),
    }

    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_checks_df.to_dict(orient="records"),
    }

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
                "limitation": "proposal_only",
                "detail": "324I creates a controlled proposal package only and does not modify official mapping or override assets.",
            },
            {
                "limitation": "single_scope_candidate_only",
                "detail": "324I processes only the single 324H scope candidate with READY_FOR_CONTROLLED_PROPOSAL status.",
            },
            {
                "limitation": "future_dry_run_required",
                "detail": "The READY_FOR_DRY_RUN proposal still requires a later dry-run stage before any official patch application.",
            },
        ]
    )

    notes_markdown = "\n".join(
        [
            "# Controlled Official Proposal From 324H 324I",
            "",
            "## Decision",
            f"- {summary['decision']}",
            "",
            "## Proposal Counts",
            f"- loaded_ready_candidate_count: {summary['loaded_ready_candidate_count']}",
            f"- proposal_count: {summary['proposal_count']}",
            f"- scope_proposal_count: {summary['scope_proposal_count']}",
            f"- alias_proposal_count: {summary['alias_proposal_count']}",
            "",
            "## Target Asset Plan",
            "- scope target: data/mapping/formal_scope_rules.json::core_metric_scope_exclusions",
            f"- target_asset_plan_count: {summary['target_asset_plan_count']}",
            f"- duplicate_proposal_id_count: {summary['duplicate_proposal_id_count']}",
            f"- target_conflict_count: {summary['target_conflict_count']}",
            "",
            "## Impact Carried Forward",
            f"- expected_affected_candidate_count: {summary['expected_affected_candidate_count']}",
            f"- expected_trusted_gain: {summary['expected_trusted_gain']}",
            f"- expected_review_reduction: {summary['expected_review_reduction']}",
            f"- expected_out_of_scope_or_rejected_gain: {summary['expected_out_of_scope_or_rejected_gain']}",
            "",
            "## Notes",
            "- 324I does not apply semantic rules or write official assets.",
            "- 324I preserves 324A through 324H provenance for the single controlled proposal.",
            "- Historical duplicate warning may be carried only when new duplicate delta stays at zero.",
            "",
        ]
    )

    return {
        "summary": summary,
        "qa_json": qa_json,
        "proposal_package_json": proposal_package_json,
        "proposal_overview_df": proposal_overview_df,
        "alias_proposals_df": alias_proposals_df,
        "scope_proposals_df": scope_proposals_df,
        "target_asset_plan_df": target_asset_plan_df,
        "proposal_source_bridge_df": proposal_source_bridge_df,
        "provenance_samples_df": provenance_samples_df,
        "qa_checks_df": qa_checks_df,
        "qa_summary_df": qa_summary_df,
        "known_limitations_df": known_limitations_df,
        "notes_markdown": notes_markdown,
    }
