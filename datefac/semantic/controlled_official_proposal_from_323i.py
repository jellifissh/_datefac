from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

import pandas as pd


EXPECTED_323I_DECISION = (
    "OFFICIAL_RULE_CANDIDATES_FROM_SANDBOX_323I_READY_FOR_323J_CONTROLLED_PROPOSAL"
)
EXPECTED_NEXT_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_323J_READY_FOR_323K_DRY_RUN"
NOT_READY_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_323J_NOT_READY"

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


def _dedupe_preserve(items: Iterable[Any]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for item in items:
        clean = _norm(item)
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _join_unique(items: Iterable[Any], limit: int = 8) -> str:
    return " | ".join(_dedupe_preserve(items)[:limit])


def _split_pipe(value: Any) -> List[str]:
    text = _norm(value)
    if not text:
        return []
    return [item.strip() for item in text.split("|") if item.strip()]


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
                }
            )
    return bool(payload), payload, pd.DataFrame(rows).fillna("")


def load_controlled_official_proposal_from_323i_inputs(
    official_rule_candidate_dir: Path,
    sandbox_replay_dir: Path,
) -> Dict[str, Any]:
    package_json = _read_json(
        official_rule_candidate_dir
        / "official_rule_candidates_from_323h_323i_candidate_package.json"
    )
    effective_candidates = package_json.get("effective_unique_candidates", [])
    candidate_source_bridge = package_json.get("candidate_source_bridge", [])
    return {
        "official_rule_candidate_summary": _read_json(
            official_rule_candidate_dir
            / "official_rule_candidates_from_323h_323i_summary.json"
        ),
        "official_rule_candidate_qa": _read_json(
            official_rule_candidate_dir / "official_rule_candidates_from_323h_323i_qa.json"
        ),
        "effective_candidates_df": pd.DataFrame(
            effective_candidates if isinstance(effective_candidates, list) else []
        ).fillna(""),
        "candidate_source_bridge_df": pd.DataFrame(
            candidate_source_bridge if isinstance(candidate_source_bridge, list) else []
        ).fillna(""),
        "source_provenance_df": _read_jsonl(
            official_rule_candidate_dir
            / "official_rule_candidates_from_323h_323i_source_provenance.jsonl"
        ),
        "sandbox_summary": _read_json(
            sandbox_replay_dir / "human_confirmed_sandbox_replay_323h_summary.json"
        ),
        "sandbox_qa": _read_json(
            sandbox_replay_dir / "human_confirmed_sandbox_replay_323h_qa.json"
        ),
        "sandbox_rule_set": _read_json(
            sandbox_replay_dir / "human_confirmed_sandbox_replay_323h_sandbox_rule_set.json"
        ),
    }


def _source_rule_lookup_from_323h(sandbox_rule_set: Dict[str, Any]) -> Set[str]:
    source_rule_ids: Set[str] = set()
    for key in ["alias_rules", "scope_rules"]:
        for item in sandbox_rule_set.get(key, []):
            if isinstance(item, dict):
                source_rule_ids.add(_norm(item.get("source_rule_id")))
    return source_rule_ids


def _target_plan_for_candidate(
    candidate_type: str,
    proposal_row: Dict[str, Any],
    alias_reference_df: pd.DataFrame,
    scope_reference_df: pd.DataFrame,
) -> Dict[str, Any]:
    if candidate_type == "alias":
        metric_family = _norm(proposal_row.get("proposed_metric_family")) or "unknown_family"
        target_group_exists = False
        if not alias_reference_df.empty and "group_name" in alias_reference_df.columns:
            target_group_exists = metric_family in set(
                alias_reference_df["group_name"].astype(str).tolist()
            )
        existing_rows = alias_reference_df.loc[
            alias_reference_df["normalized_label_key"].astype(str)
            == _normalize_label(proposal_row.get("normalized_label"))
        ].copy() if not alias_reference_df.empty else pd.DataFrame()
        overlap_status = "NO_OFFICIAL_OVERLAP"
        conflict_status = "NO_TARGET_CONFLICT"
        if not existing_rows.empty:
            existing_metric_codes = _dedupe_preserve(existing_rows["metric_code"].tolist())
            if _norm(proposal_row.get("proposed_metric_code")) in existing_metric_codes:
                overlap_status = "ALREADY_OFFICIAL_SAME_ALIAS"
            else:
                overlap_status = "ALREADY_OFFICIAL_DIFFERENT_ALIAS"
                conflict_status = "TARGET_CONFLICT_EXISTING_ALIAS"
        return {
            "target_asset_path": str(OFFICIAL_ALIAS_ASSET_PATH),
            "target_rule_family": "semantic_alias_candidates",
            "target_asset_exists": OFFICIAL_ALIAS_ASSET_PATH.exists(),
            "target_group_name": metric_family,
            "target_group_exists_or_virtual": target_group_exists,
            "target_group_resolution": (
                "EXISTING_GROUP" if target_group_exists else "MISSING_GROUP"
            ),
            "future_operation_type": "APPEND_ALIAS_ENTRY",
            "intended_future_target_file_or_rule_group": (
                f"data/overrides/semantic_alias_candidates.json::{metric_family}"
            ),
            "target_official_rule_category": "official_alias_mapping_candidate",
            "already_official_overlap_status": overlap_status,
            "target_conflict_status": conflict_status,
        }

    target_group_exists = False
    if not scope_reference_df.empty and "target_group" in scope_reference_df.columns:
        target_group_exists = "core_metric_scope_exclusions" in set(
            scope_reference_df["target_group"].astype(str).tolist()
        )
    existing_rows = scope_reference_df.loc[
        scope_reference_df["normalized_label_key"].astype(str)
        == _normalize_label(proposal_row.get("normalized_label"))
    ].copy() if not scope_reference_df.empty else pd.DataFrame()
    overlap_status = "NO_OFFICIAL_OVERLAP"
    conflict_status = "NO_TARGET_CONFLICT"
    if not existing_rows.empty:
        existing_actions = _dedupe_preserve(existing_rows["scope_action"].tolist())
        if _norm(proposal_row.get("proposed_scope_action")) in existing_actions:
            overlap_status = "ALREADY_OFFICIAL_SAME_SCOPE_RULE"
        else:
            overlap_status = "ALREADY_OFFICIAL_DIFFERENT_SCOPE_RULE"
            conflict_status = "TARGET_CONFLICT_EXISTING_SCOPE_RULE"
    return {
        "target_asset_path": str(FORMAL_SCOPE_RULES_PATH),
        "target_rule_family": "formal_scope_rules",
        "target_asset_exists": FORMAL_SCOPE_RULES_PATH.exists(),
        "target_group_name": "core_metric_scope_exclusions",
        "target_group_exists_or_virtual": target_group_exists,
        "target_group_resolution": (
            "EXISTING_GROUP" if target_group_exists else "MISSING_GROUP"
        ),
        "future_operation_type": "APPEND_SCOPE_EXCLUSION_RULE",
        "intended_future_target_file_or_rule_group": (
            "data/mapping/formal_scope_rules.json::core_metric_scope_exclusions"
        ),
        "target_official_rule_category": "official_scope_rule_candidate",
        "already_official_overlap_status": overlap_status,
        "target_conflict_status": conflict_status,
    }


def build_controlled_official_proposal_from_323i(
    official_rule_candidate_summary: Dict[str, Any],
    official_rule_candidate_qa: Dict[str, Any],
    effective_candidates_df: pd.DataFrame,
    candidate_source_bridge_df: pd.DataFrame,
    source_provenance_df: pd.DataFrame,
    sandbox_summary: Dict[str, Any],
    sandbox_qa: Dict[str, Any],
    sandbox_rule_set: Dict[str, Any],
    alias_reference_loaded: bool,
    alias_reference_df: pd.DataFrame,
    scope_reference_loaded: bool,
    scope_reference_df: pd.DataFrame,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa(
        "readiness::323i_decision",
        "PASS"
        if _norm(official_rule_candidate_summary.get("decision")) == EXPECTED_323I_DECISION
        else "FAIL",
        _norm(official_rule_candidate_summary.get("decision")),
    )
    add_qa(
        "readiness::323i_qa_fail_count",
        "PASS" if _safe_int(official_rule_candidate_summary.get("qa_fail_count")) == 0 else "FAIL",
        str(official_rule_candidate_summary.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::323i_qa_json_fail_count",
        "PASS" if _safe_int(official_rule_candidate_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(official_rule_candidate_qa.get("qa_fail_count", "")),
    )
    for key, expected in [
        ("effective_unique_candidate_count", 6),
        ("alias_candidate_count", 2),
        ("scope_candidate_count", 4),
        ("ready_for_controlled_proposal_count", 6),
        ("needs_review_candidate_count", 0),
        ("rejected_candidate_count", 0),
        ("affected_candidate_count", 129),
        ("trusted_gain_323i", 44),
        ("review_reduction_323i", 129),
        ("out_of_scope_or_rejected_gain_323i", 85),
    ]:
        add_qa(
            f"readiness::323i_{key}",
            "PASS" if _safe_int(official_rule_candidate_summary.get(key)) == expected else "FAIL",
            f"expected={expected} actual={official_rule_candidate_summary.get(key, '')}",
        )

    ready_candidates_df = effective_candidates_df.loc[
        effective_candidates_df["rule_candidate_status"].astype(str)
        == "READY_FOR_CONTROLLED_PROPOSAL"
    ].copy() if not effective_candidates_df.empty else pd.DataFrame()
    ready_candidates_df = ready_candidates_df.sort_values(
        ["candidate_type", "normalized_label_key"], ascending=[True, True]
    ).reset_index(drop=True)

    add_qa(
        "inputs::loaded_ready_candidate_count",
        "PASS" if len(ready_candidates_df) == 6 else "FAIL",
        f"actual={len(ready_candidates_df)}",
    )
    add_qa(
        "inputs::loaded_ready_alias_candidate_count",
        "PASS"
        if int(ready_candidates_df["candidate_type"].astype(str).eq("alias").sum()) == 2
        else "FAIL",
        f"actual={int(ready_candidates_df['candidate_type'].astype(str).eq('alias').sum()) if not ready_candidates_df.empty else 0}",
    )
    add_qa(
        "inputs::loaded_ready_scope_candidate_count",
        "PASS"
        if int(ready_candidates_df["candidate_type"].astype(str).eq("scope").sum()) == 4
        else "FAIL",
        f"actual={int(ready_candidates_df['candidate_type'].astype(str).eq('scope').sum()) if not ready_candidates_df.empty else 0}",
    )

    source_rule_ids_in_323h = _source_rule_lookup_from_323h(sandbox_rule_set)

    proposal_rows: List[Dict[str, Any]] = []
    alias_rows: List[Dict[str, Any]] = []
    scope_rows: List[Dict[str, Any]] = []
    target_plan_rows: List[Dict[str, Any]] = []
    duplicate_provenance_bridge_rows: List[Dict[str, Any]] = []
    provenance_sample_rows: List[Dict[str, Any]] = []

    alias_index = 0
    scope_index = 0

    for _, row in ready_candidates_df.iterrows():
        row_dict = row.to_dict()
        candidate_type = _norm(row_dict.get("candidate_type"))
        if candidate_type == "alias":
            alias_index += 1
            proposal_id = f"proposal_323j::alias::{alias_index:03d}"
        else:
            scope_index += 1
            proposal_id = f"proposal_323j::scope::{scope_index:03d}"

        bridge_df = candidate_source_bridge_df.loc[
            candidate_source_bridge_df["rule_candidate_id"].astype(str)
            == _norm(row_dict.get("rule_candidate_id"))
        ].copy() if not candidate_source_bridge_df.empty else pd.DataFrame()
        source_rule_ids = _dedupe_preserve(bridge_df.get("source_rule_id", pd.Series(dtype=str)).tolist())
        confirmation_ids = _dedupe_preserve(bridge_df.get("confirmation_id", pd.Series(dtype=str)).tolist())
        request_ids = _dedupe_preserve(bridge_df.get("request_id", pd.Series(dtype=str)).tolist())
        source_group_ids = _dedupe_preserve(bridge_df.get("source_group_id", pd.Series(dtype=str)).tolist())

        provenance_df = source_provenance_df.loc[
            source_provenance_df["source_rule_id"].astype(str).isin(source_rule_ids)
        ].copy() if not source_provenance_df.empty else pd.DataFrame()

        target_plan = _target_plan_for_candidate(
            candidate_type=candidate_type,
            proposal_row=row_dict,
            alias_reference_df=alias_reference_df,
            scope_reference_df=scope_reference_df,
        )

        overlap_status = _norm(target_plan.get("already_official_overlap_status"))
        conflict_status = _norm(target_plan.get("target_conflict_status"))
        missing_target_asset_or_group = (
            not _safe_bool(target_plan.get("target_asset_exists"))
            or not _safe_bool(target_plan.get("target_group_exists_or_virtual"))
        )
        missing_provenance = (
            not source_rule_ids
            or not confirmation_ids
            or not request_ids
            or provenance_df.empty
        )
        proposal_status = (
            "REJECTED"
            if conflict_status.startswith("TARGET_CONFLICT")
            else "NEEDS_REVIEW"
            if overlap_status.startswith("ALREADY_OFFICIAL")
            or missing_target_asset_or_group
            or missing_provenance
            else "READY_FOR_DRY_RUN"
        )

        rollback_note = (
            f"Before any future dry run/application, remove alias proposal '{proposal_id}' for label '{_norm(row_dict.get('normalized_label'))}' from the controlled proposal package."
            if candidate_type == "alias"
            else f"Before any future dry run/application, remove scope proposal '{proposal_id}' for label '{_norm(row_dict.get('normalized_label'))}' from the controlled proposal package."
        )

        proposal_row = {
            "controlled_proposal_id": proposal_id,
            "source_rule_candidate_id": _norm(row_dict.get("rule_candidate_id")),
            "candidate_type": candidate_type,
            "proposal_type": _norm(row_dict.get("proposal_type")),
            "proposal_status": proposal_status,
            "normalized_label": _norm(row_dict.get("normalized_label")),
            "normalized_label_key": _norm(row_dict.get("normalized_label_key")),
            "source_rule_count": _safe_int(row_dict.get("source_rule_count")),
            "duplicate_source_rule": _safe_bool(row_dict.get("duplicate_source_rule")),
            "dedupe_resolution": _norm(row_dict.get("dedupe_resolution")),
            "duplicate_provenance_retained_only": True,
            "source_rule_ids": "|".join(source_rule_ids),
            "source_confirmation_ids": "|".join(confirmation_ids),
            "source_request_ids": "|".join(request_ids),
            "source_group_ids": "|".join(source_group_ids),
            "reviewer_names": _norm(row_dict.get("reviewer_names")),
            "reviewer_notes": _norm(row_dict.get("reviewer_notes")),
            "review_timestamps": _norm(row_dict.get("review_timestamps")),
            "proposed_metric_code": _norm(row_dict.get("proposed_metric_code")),
            "proposed_metric_family": _norm(row_dict.get("proposed_metric_family")),
            "proposed_scope_action": _norm(row_dict.get("proposed_scope_action")),
            "target_label_examples": _norm(row_dict.get("target_label_examples")),
            "expected_affected_candidate_count": _safe_int(
                row_dict.get("actual_affected_candidate_count")
                or row_dict.get("expected_affected_candidate_count")
            ),
            "expected_trusted_gain": _safe_int(row_dict.get("trusted_gain")),
            "expected_review_reduction": _safe_int(row_dict.get("review_reduction")),
            "expected_out_of_scope_or_rejected_gain": _safe_int(
                row_dict.get("out_of_scope_or_rejected_gain")
            ),
            "priority_score_max": row_dict.get("priority_score_max"),
            "priority_score_sum": row_dict.get("priority_score_sum"),
            "risk_flags": _norm(row_dict.get("risk_flags")),
            "sample_table_titles": _norm(row_dict.get("sample_table_titles")),
            "sample_texts": _norm(row_dict.get("sample_texts")),
            "sample_years": _norm(row_dict.get("sample_years")),
            "provenance_text_samples": _norm(row_dict.get("provenance_text_samples")),
            "candidate_readiness_reason": _norm(row_dict.get("candidate_readiness_reason")),
            "target_asset_path": _norm(target_plan.get("target_asset_path")),
            "target_rule_family": _norm(target_plan.get("target_rule_family")),
            "target_asset_exists": _safe_bool(target_plan.get("target_asset_exists")),
            "target_group_name": _norm(target_plan.get("target_group_name")),
            "target_group_exists_or_virtual": _safe_bool(
                target_plan.get("target_group_exists_or_virtual")
            ),
            "target_group_resolution": _norm(target_plan.get("target_group_resolution")),
            "future_operation_type": _norm(target_plan.get("future_operation_type")),
            "target_official_rule_category": _norm(
                target_plan.get("target_official_rule_category")
            ),
            "intended_future_target_file_or_rule_group": _norm(
                target_plan.get("intended_future_target_file_or_rule_group")
            ),
            "already_official_overlap_status": overlap_status,
            "target_conflict_status": conflict_status,
            "rollback_note": rollback_note,
            "eligible_for_323k_dry_run": proposal_status == "READY_FOR_DRY_RUN",
            "proposal_only_no_apply_confirmed": True,
        }
        proposal_rows.append(proposal_row)

        target_plan_rows.append(
            {
                "controlled_proposal_id": proposal_id,
                "candidate_type": candidate_type,
                "normalized_label": proposal_row["normalized_label"],
                "target_asset_path": proposal_row["target_asset_path"],
                "target_rule_family": proposal_row["target_rule_family"],
                "target_group_name": proposal_row["target_group_name"],
                "target_group_resolution": proposal_row["target_group_resolution"],
                "future_operation_type": proposal_row["future_operation_type"],
                "target_official_rule_category": proposal_row["target_official_rule_category"],
                "already_official_overlap_status": overlap_status,
                "target_conflict_status": conflict_status,
                "eligible_for_323k_dry_run": proposal_row["eligible_for_323k_dry_run"],
            }
        )

        for _, bridge_row in bridge_df.iterrows():
            duplicate_provenance_bridge_rows.append(
                {
                    "controlled_proposal_id": proposal_id,
                    "source_rule_candidate_id": _norm(row_dict.get("rule_candidate_id")),
                    "duplicate_source_rule": _safe_bool(row_dict.get("duplicate_source_rule")),
                    "source_rule_id": _norm(bridge_row.get("source_rule_id")),
                    "source_rule_exists_in_323h_sandbox_rule_set": _norm(
                        bridge_row.get("source_rule_id")
                    )
                    in source_rule_ids_in_323h,
                    "confirmation_id": _norm(bridge_row.get("confirmation_id")),
                    "request_id": _norm(bridge_row.get("request_id")),
                    "source_group_id": _norm(bridge_row.get("source_group_id")),
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
            provenance_sample_rows.append(
                {
                    "controlled_proposal_id": proposal_id,
                    "source_rule_id": _norm(prov_row.get("source_rule_id")),
                    "confirmation_id": _norm(prov_row.get("confirmation_id")),
                    "request_id": _norm(prov_row.get("request_id")),
                    "source_group_id": _norm(prov_row.get("source_group_id")),
                    "sample_candidate_ids": _norm(prov_row.get("sample_candidate_ids")),
                    "sample_table_titles": _norm(prov_row.get("sample_table_titles")),
                    "sample_texts": _norm(prov_row.get("sample_texts")),
                    "sample_years": _norm(prov_row.get("sample_years")),
                    "sample_evidence_text": _norm(prov_row.get("sample_evidence_text")),
                    "provenance_text": _norm(prov_row.get("provenance_text")),
                    "application_status": _norm(prov_row.get("application_status")),
                }
            )

    proposal_overview_df = pd.DataFrame(proposal_rows).fillna("")
    alias_proposals_df = proposal_overview_df.loc[
        proposal_overview_df["candidate_type"].astype(str) == "alias"
    ].copy() if not proposal_overview_df.empty else pd.DataFrame()
    scope_proposals_df = proposal_overview_df.loc[
        proposal_overview_df["candidate_type"].astype(str) == "scope"
    ].copy() if not proposal_overview_df.empty else pd.DataFrame()
    target_asset_plan_df = pd.DataFrame(target_plan_rows).fillna("")
    duplicate_provenance_bridge_df = pd.DataFrame(duplicate_provenance_bridge_rows).fillna("")
    provenance_samples_df = pd.DataFrame(provenance_sample_rows).fillna("")

    duplicate_proposal_id_count = int(
        proposal_overview_df["controlled_proposal_id"].astype(str).duplicated().sum()
    ) if not proposal_overview_df.empty else 0
    already_official_overlap_count = int(
        proposal_overview_df["already_official_overlap_status"]
        .astype(str)
        .str.startswith("ALREADY_OFFICIAL")
        .sum()
    ) if not proposal_overview_df.empty else 0
    target_conflict_count = int(
        proposal_overview_df["target_conflict_status"]
        .astype(str)
        .str.startswith("TARGET_CONFLICT")
        .sum()
    ) if not proposal_overview_df.empty else 0
    missing_target_asset_or_group_count = int(
        (
            ~proposal_overview_df["target_asset_exists"].astype(bool)
            | ~proposal_overview_df["target_group_exists_or_virtual"].astype(bool)
        ).sum()
    ) if not proposal_overview_df.empty else 0
    missing_provenance_count = int(
        proposal_overview_df[
            proposal_overview_df["source_rule_ids"].astype(str).eq("")
            | proposal_overview_df["source_confirmation_ids"].astype(str).eq("")
            | proposal_overview_df["source_request_ids"].astype(str).eq("")
        ].shape[0]
    ) if not proposal_overview_df.empty else 0
    ready_proposal_count = int(
        proposal_overview_df["proposal_status"].astype(str).eq("READY_FOR_DRY_RUN").sum()
    ) if not proposal_overview_df.empty else 0
    review_proposal_count = int(
        proposal_overview_df["proposal_status"].astype(str).eq("NEEDS_REVIEW").sum()
    ) if not proposal_overview_df.empty else 0
    rejected_proposal_count = int(
        proposal_overview_df["proposal_status"].astype(str).eq("REJECTED").sum()
    ) if not proposal_overview_df.empty else 0

    add_qa(
        "proposal_counts::total",
        "PASS" if len(proposal_overview_df) == 6 else "FAIL",
        f"actual={len(proposal_overview_df)}",
    )
    add_qa(
        "proposal_counts::alias",
        "PASS" if len(alias_proposals_df) == 2 else "FAIL",
        f"actual={len(alias_proposals_df)}",
    )
    add_qa(
        "proposal_counts::scope",
        "PASS" if len(scope_proposals_df) == 4 else "FAIL",
        f"actual={len(scope_proposals_df)}",
    )
    add_qa(
        "proposal_counts::ready",
        "PASS" if ready_proposal_count == 6 else "FAIL",
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
        "provenance::bridge_rows_preserved_without_reexpansion",
        "PASS"
        if len(duplicate_provenance_bridge_df) == 11 and len(proposal_overview_df) == 6
        else "FAIL",
        f"bridge_rows={len(duplicate_provenance_bridge_df)} proposals={len(proposal_overview_df)}",
    )
    add_qa(
        "provenance::all_bridge_source_rules_trace_to_323h",
        "PASS"
        if duplicate_provenance_bridge_df.empty
        or duplicate_provenance_bridge_df[
            "source_rule_exists_in_323h_sandbox_rule_set"
        ].astype(bool).all()
        else "FAIL",
        f"bridge_rows={len(duplicate_provenance_bridge_df)}",
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
        "impact::affected_candidate_count_carried_forward",
        "PASS" if expected_affected_candidate_count == 129 else "FAIL",
        f"actual={expected_affected_candidate_count}",
    )
    add_qa(
        "impact::trusted_gain_carried_forward",
        "PASS" if expected_trusted_gain == 44 else "FAIL",
        f"actual={expected_trusted_gain}",
    )
    add_qa(
        "impact::review_reduction_carried_forward",
        "PASS" if expected_review_reduction == 129 else "FAIL",
        f"actual={expected_review_reduction}",
    )
    add_qa(
        "impact::out_of_scope_gain_carried_forward",
        "PASS" if expected_out_of_scope_or_rejected_gain == 85 else "FAIL",
        f"actual={expected_out_of_scope_or_rejected_gain}",
    )

    add_qa(
        "safety::official_alias_asset_reference_loaded",
        "PASS" if alias_reference_loaded else "FAIL",
        str(OFFICIAL_ALIAS_ASSET_PATH),
    )
    add_qa(
        "safety::formal_scope_rules_reference_loaded",
        "PASS" if scope_reference_loaded else "FAIL",
        str(FORMAL_SCOPE_RULES_PATH),
    )
    add_qa(
        "safety::323h_core_false_exclusion_count_zero",
        "PASS" if _safe_int(sandbox_summary.get("core_false_exclusion_count")) == 0 else "FAIL",
        str(sandbox_summary.get("core_false_exclusion_count", "")),
    )
    add_qa(
        "safety::323h_conflict_count_zero",
        "PASS" if _safe_int(sandbox_summary.get("conflict_count")) == 0 else "FAIL",
        str(sandbox_summary.get("conflict_count", "")),
    )
    add_qa(
        "safety::proposal_only_no_apply_confirmed",
        "PASS",
        "323J builds proposal records only and does not apply semantic rules.",
    )
    add_qa(
        "safety::no_llm_or_api_call_executed",
        "PASS",
        "323J uses 323I outputs and cached 323H evidence only.",
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
        "stage": "323J",
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
        "target_conflict_count": target_conflict_count,
        "missing_target_asset_or_group_count": missing_target_asset_or_group_count,
        "missing_provenance_count": missing_provenance_count,
        "expected_affected_candidate_count": expected_affected_candidate_count,
        "expected_trusted_gain": expected_trusted_gain,
        "expected_review_reduction": expected_review_reduction,
        "expected_out_of_scope_or_rejected_gain": expected_out_of_scope_or_rejected_gain,
        "proposal_only_no_apply_confirmed": True,
        "official_assets_not_modified_confirmed": True,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": EXPECTED_NEXT_DECISION if qa_fail_count == 0 else NOT_READY_DECISION,
    }

    proposal_package_json = {
        "stage": "323J",
        "decision": summary["decision"],
        "source_readiness_summary": {
            "official_rule_candidate_decision": _norm(
                official_rule_candidate_summary.get("decision")
            ),
            "sandbox_replay_decision": _norm(sandbox_summary.get("decision")),
            "loaded_ready_candidate_count": summary["loaded_ready_candidate_count"],
        },
        "controlled_proposals": proposal_overview_df.to_dict(orient="records"),
        "alias_proposals": alias_proposals_df.to_dict(orient="records"),
        "scope_proposals": scope_proposals_df.to_dict(orient="records"),
        "target_asset_plan": target_asset_plan_df.to_dict(orient="records"),
        "duplicate_provenance_bridge": duplicate_provenance_bridge_df.to_dict(
            orient="records"
        ),
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
                "detail": "323J creates a controlled proposal package only and does not modify official mapping or override assets.",
            },
            {
                "limitation": "dedupe_preserved",
                "detail": "Duplicate source suggestions remain provenance only and are not re-expanded back into separate proposal records.",
            },
            {
                "limitation": "future_stage_required",
                "detail": "All READY_FOR_DRY_RUN proposals still require a later dry-run stage before any official patch application.",
            },
        ]
    )

    notes_lines = [
        "# Controlled Official Proposal 323J",
        "",
        "## Decision",
        f"- {summary['decision']}",
        "",
        "## Proposal Counts",
        f"- loaded_ready_candidate_count: {summary['loaded_ready_candidate_count']}",
        f"- proposal_count: {summary['proposal_count']}",
        f"- alias_proposal_count: {summary['alias_proposal_count']}",
        f"- scope_proposal_count: {summary['scope_proposal_count']}",
        "",
        "## Target Asset Plan",
        f"- target_asset_file_count: {summary['target_asset_file_count']}",
        f"- alias target: data/overrides/semantic_alias_candidates.json::profitability",
        f"- scope target: data/mapping/formal_scope_rules.json::core_metric_scope_exclusions",
        "",
        "## Impact Carried Forward",
        f"- expected_affected_candidate_count: {summary['expected_affected_candidate_count']}",
        f"- expected_trusted_gain: {summary['expected_trusted_gain']}",
        f"- expected_review_reduction: {summary['expected_review_reduction']}",
        f"- expected_out_of_scope_or_rejected_gain: {summary['expected_out_of_scope_or_rejected_gain']}",
        "",
        "## Proposal-Only Note",
        "- 323J does not apply semantic rules.",
        "- Duplicate source suggestions are retained as provenance only.",
        "",
    ]
    notes_markdown = "\n".join(notes_lines)

    return {
        "summary": summary,
        "qa_json": qa_json,
        "proposal_package_json": proposal_package_json,
        "proposal_overview_df": proposal_overview_df,
        "alias_proposals_df": alias_proposals_df,
        "scope_proposals_df": scope_proposals_df,
        "target_asset_plan_df": target_asset_plan_df,
        "duplicate_provenance_bridge_df": duplicate_provenance_bridge_df,
        "provenance_samples_df": provenance_samples_df,
        "qa_checks_df": qa_checks_df,
        "qa_summary_df": qa_summary_df,
        "known_limitations_df": known_limitations_df,
        "notes_markdown": notes_markdown,
    }
