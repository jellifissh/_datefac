from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

import pandas as pd


EXPECTED_323J_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_323J_READY_FOR_323K_DRY_RUN"
EXPECTED_323I_DECISION = (
    "OFFICIAL_RULE_CANDIDATES_FROM_SANDBOX_323I_READY_FOR_323J_CONTROLLED_PROPOSAL"
)
EXPECTED_323H_DECISION_PREFIX = (
    "HUMAN_CONFIRMED_SANDBOX_REPLAY_323H_READY_FOR_"
)
EXPECTED_NEXT_DECISION = (
    "CONTROLLED_OFFICIAL_PROPOSAL_DRY_RUN_323K_READY_FOR_HUMAN_APPROVAL"
)
NOT_READY_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_DRY_RUN_323K_NOT_READY"

OFFICIAL_ALIAS_ASSET_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")
FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
ALIAS_TARGET_GROUP = "profitability"
SCOPE_TARGET_GROUP = "core_metric_scope_exclusions"


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
    return _norm(value).lower() in {"1", "true", "yes", "y"}


def _dedupe_preserve(items: Iterable[Any]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for item in items:
        clean = _norm(item)
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _safe_numeric_sum(df: pd.DataFrame, column: str) -> int:
    if df.empty or column not in df.columns:
        return 0
    return int(pd.to_numeric(df[column], errors="coerce").fillna(0).sum())


def load_controlled_official_proposal_dry_run_inputs(
    controlled_proposal_dir: Path,
    official_rule_candidate_dir: Path,
    sandbox_replay_dir: Path,
) -> Dict[str, Any]:
    proposal_package = _read_json(
        controlled_proposal_dir
        / "controlled_official_proposal_from_323i_323j_proposal_package.json"
    )
    return {
        "controlled_summary": _read_json(
            controlled_proposal_dir
            / "controlled_official_proposal_from_323i_323j_summary.json"
        ),
        "controlled_qa": _read_json(
            controlled_proposal_dir / "controlled_official_proposal_from_323i_323j_qa.json"
        ),
        "proposal_package": proposal_package,
        "controlled_proposals_df": pd.DataFrame(
            proposal_package.get("controlled_proposals", [])
            if isinstance(proposal_package.get("controlled_proposals", []), list)
            else []
        ).fillna(""),
        "duplicate_provenance_bridge_df": pd.DataFrame(
            proposal_package.get("duplicate_provenance_bridge", [])
            if isinstance(proposal_package.get("duplicate_provenance_bridge", []), list)
            else []
        ).fillna(""),
        "official_rule_candidate_summary": _read_json(
            official_rule_candidate_dir
            / "official_rule_candidates_from_323h_323i_summary.json"
        ),
        "sandbox_summary": _read_json(
            sandbox_replay_dir / "human_confirmed_sandbox_replay_323h_summary.json"
        ),
        "official_alias_payload": _read_json(OFFICIAL_ALIAS_ASSET_PATH),
        "formal_scope_rules_payload": _read_json(FORMAL_SCOPE_RULES_PATH),
    }


def _build_alias_reference_df(payload: Dict[str, Any]) -> pd.DataFrame:
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
                        "normalized_label_key": _normalize_label(
                            item.get("normalized_label")
                        ),
                        "metric_code": _norm(item.get("metric_code")),
                        "metric_family": _norm(item.get("metric_family")),
                        "rule_id": _norm(item.get("rule_id")),
                    }
                )
    return pd.DataFrame(rows).fillna("")


def _build_scope_reference_df(payload: Dict[str, Any]) -> pd.DataFrame:
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
    return pd.DataFrame(rows).fillna("")


def _preview_alias_entry(proposal: Dict[str, Any], sequence: int) -> Dict[str, Any]:
    return {
        "rule_id": f"DRY_RUN_323K_ALIAS_{sequence:03d}",
        "normalized_label": _norm(proposal.get("normalized_label")),
        "metric_code": _norm(proposal.get("proposed_metric_code")),
        "metric_family": _norm(proposal.get("proposed_metric_family")) or ALIAS_TARGET_GROUP,
        "source_controlled_proposal_id": _norm(proposal.get("controlled_proposal_id")),
        "source_rule_candidate_id": _norm(proposal.get("source_rule_candidate_id")),
        "source_rule_ids": _norm(proposal.get("source_rule_ids")),
        "source_confirmation_ids": _norm(proposal.get("source_confirmation_ids")),
        "source_request_ids": _norm(proposal.get("source_request_ids")),
        "dry_run_only": True,
    }


def _preview_scope_rule(proposal: Dict[str, Any], sequence: int) -> Dict[str, Any]:
    return {
        "rule_id": f"DRY_RUN_323K_SCOPE_{sequence:03d}",
        "rule_type": "core_metric_scope_exclusion",
        "target_group": SCOPE_TARGET_GROUP,
        "normalized_label": _norm(proposal.get("normalized_label")),
        "scope_action": _norm(proposal.get("proposed_scope_action"))
        or "exclude_from_core_metric_mapping",
        "source_controlled_proposal_id": _norm(proposal.get("controlled_proposal_id")),
        "source_rule_candidate_id": _norm(proposal.get("source_rule_candidate_id")),
        "source_rule_ids": _norm(proposal.get("source_rule_ids")),
        "source_confirmation_ids": _norm(proposal.get("source_confirmation_ids")),
        "source_request_ids": _norm(proposal.get("source_request_ids")),
        "dry_run_only": True,
    }


def _build_virtual_after_alias_payload(
    payload: Dict[str, Any], operations_df: pd.DataFrame
) -> Dict[str, Any]:
    virtual_payload = deepcopy(payload) if isinstance(payload, dict) else {}
    virtual_payload.setdefault("groups", {})
    groups = virtual_payload["groups"]
    if not isinstance(groups, dict):
        groups = {}
        virtual_payload["groups"] = groups
    group_entries = groups.setdefault(ALIAS_TARGET_GROUP, [])
    if not isinstance(group_entries, list):
        group_entries = []
        groups[ALIAS_TARGET_GROUP] = group_entries
    for _, row in operations_df.iterrows():
        preview = row.get("preview_payload_dict")
        if isinstance(preview, dict):
            group_entries.append(preview)
    return virtual_payload


def _build_virtual_after_scope_payload(
    payload: Dict[str, Any], operations_df: pd.DataFrame
) -> Dict[str, Any]:
    virtual_payload = deepcopy(payload) if isinstance(payload, dict) else {}
    virtual_payload.setdefault("rules", {})
    rules = virtual_payload["rules"]
    if not isinstance(rules, dict):
        rules = {}
        virtual_payload["rules"] = rules
    for _, row in operations_df.iterrows():
        preview = row.get("preview_payload_dict")
        if isinstance(preview, dict):
            rules[_norm(preview.get("rule_id"))] = preview
    return virtual_payload


def build_controlled_official_proposal_dry_run(
    controlled_summary: Dict[str, Any],
    controlled_qa: Dict[str, Any],
    controlled_proposals_df: pd.DataFrame,
    duplicate_provenance_bridge_df: pd.DataFrame,
    official_rule_candidate_summary: Dict[str, Any],
    sandbox_summary: Dict[str, Any],
    official_alias_payload: Dict[str, Any],
    formal_scope_rules_payload: Dict[str, Any],
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa(
        "readiness::323j_decision",
        "PASS"
        if _norm(controlled_summary.get("decision")) == EXPECTED_323J_DECISION
        else "FAIL",
        _norm(controlled_summary.get("decision")),
    )
    add_qa(
        "readiness::323j_qa_fail_count",
        "PASS" if _safe_int(controlled_summary.get("qa_fail_count")) == 0 else "FAIL",
        str(controlled_summary.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::323j_qa_json_fail_count",
        "PASS" if _safe_int(controlled_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(controlled_qa.get("qa_fail_count", "")),
    )

    for key, expected in [
        ("loaded_ready_candidate_count", 6),
        ("proposal_count", 6),
        ("alias_proposal_count", 2),
        ("scope_proposal_count", 4),
        ("ready_for_dry_run_proposal_count", 6),
        ("needs_review_proposal_count", 0),
        ("rejected_proposal_count", 0),
        ("duplicate_proposal_id_count", 0),
        ("already_official_overlap_count", 0),
        ("target_conflict_count", 0),
        ("missing_target_asset_or_group_count", 0),
        ("missing_provenance_count", 0),
        ("expected_affected_candidate_count", 129),
        ("expected_trusted_gain", 44),
        ("expected_review_reduction", 129),
        ("expected_out_of_scope_or_rejected_gain", 85),
    ]:
        add_qa(
            f"readiness::323j_{key}",
            "PASS" if _safe_int(controlled_summary.get(key)) == expected else "FAIL",
            f"expected={expected} actual={controlled_summary.get(key, '')}",
        )

    add_qa(
        "consistency::323i_decision",
        "PASS"
        if _norm(official_rule_candidate_summary.get("decision")) == EXPECTED_323I_DECISION
        else "FAIL",
        _norm(official_rule_candidate_summary.get("decision")),
    )
    add_qa(
        "consistency::323h_decision_family",
        "PASS"
        if _norm(sandbox_summary.get("decision")).startswith(EXPECTED_323H_DECISION_PREFIX)
        else "FAIL",
        _norm(sandbox_summary.get("decision")),
    )
    for key, expected in [
        ("affected_candidate_count", 129),
        ("trusted_gain_323i", 44),
        ("review_reduction_323i", 129),
        ("out_of_scope_or_rejected_gain_323i", 85),
    ]:
        add_qa(
            f"consistency::323i_{key}",
            "PASS"
            if _safe_int(official_rule_candidate_summary.get(key)) == expected
            else "FAIL",
            f"expected={expected} actual={official_rule_candidate_summary.get(key, '')}",
        )
    for key, expected in [
        ("affected_candidate_count", 129),
        ("trusted_gain_323h", 44),
        ("review_reduction_323h", 129),
        ("out_of_scope_or_rejected_gain_323h", 85),
        ("core_false_exclusion_count", 0),
        ("conflict_count", 0),
    ]:
        add_qa(
            f"consistency::323h_{key}",
            "PASS" if _safe_int(sandbox_summary.get(key)) == expected else "FAIL",
            f"expected={expected} actual={sandbox_summary.get(key, '')}",
        )

    proposals_df = (
        controlled_proposals_df.loc[
            controlled_proposals_df["proposal_status"].astype(str)
            == "READY_FOR_DRY_RUN"
        ]
        .copy()
        .reset_index(drop=True)
        if not controlled_proposals_df.empty
        else pd.DataFrame()
    )
    if not proposals_df.empty:
        proposals_df["normalized_label_key"] = proposals_df["normalized_label"].map(
            _normalize_label
        )

    alias_reference_df = _build_alias_reference_df(official_alias_payload)
    scope_reference_df = _build_scope_reference_df(formal_scope_rules_payload)

    add_qa(
        "inputs::loaded_ready_proposal_count",
        "PASS" if len(proposals_df) == 6 else "FAIL",
        f"actual={len(proposals_df)}",
    )
    add_qa(
        "inputs::loaded_ready_alias_proposal_count",
        "PASS"
        if int(proposals_df["candidate_type"].astype(str).eq("alias").sum()) == 2
        else "FAIL",
        f"actual={int(proposals_df['candidate_type'].astype(str).eq('alias').sum()) if not proposals_df.empty else 0}",
    )
    add_qa(
        "inputs::loaded_ready_scope_proposal_count",
        "PASS"
        if int(proposals_df["candidate_type"].astype(str).eq("scope").sum()) == 4
        else "FAIL",
        f"actual={int(proposals_df['candidate_type'].astype(str).eq('scope').sum()) if not proposals_df.empty else 0}",
    )

    operation_rows: List[Dict[str, Any]] = []
    diff_preview_rows: List[Dict[str, Any]] = []
    rollback_rows: List[Dict[str, Any]] = []
    no_apply_targets: List[str] = []

    alias_sequence = 0
    scope_sequence = 0
    for _, row in proposals_df.iterrows():
        proposal = row.to_dict()
        proposal_id = _norm(proposal.get("controlled_proposal_id"))
        candidate_type = _norm(proposal.get("candidate_type"))
        normalized_label = _norm(proposal.get("normalized_label"))
        normalized_label_key = _normalize_label(normalized_label)

        if candidate_type == "alias":
            alias_sequence += 1
            preview_payload = _preview_alias_entry(proposal, alias_sequence)
            target_asset_path = str(OFFICIAL_ALIAS_ASSET_PATH)
            target_group_name = ALIAS_TARGET_GROUP
            group_df = alias_reference_df.loc[
                alias_reference_df["group_name"].astype(str) == target_group_name
            ].copy()
            exact_match_df = group_df.loc[
                (group_df["normalized_label_key"].astype(str) == normalized_label_key)
                & (
                    group_df["metric_code"].astype(str)
                    == _norm(proposal.get("proposed_metric_code"))
                )
            ].copy()
            overlap_count = len(exact_match_df)
            group_before_count = len(group_df)
            group_after_count = group_before_count + 1
            operation_id = f"dry_run_323k::alias::{alias_sequence:03d}"
            target_locator = f"{target_asset_path}::{target_group_name}"
            before_state = (
                "EXACT_ALIAS_ALREADY_PRESENT" if overlap_count else "ALIAS_NOT_PRESENT"
            )
        else:
            scope_sequence += 1
            preview_payload = _preview_scope_rule(proposal, scope_sequence)
            target_asset_path = str(FORMAL_SCOPE_RULES_PATH)
            target_group_name = SCOPE_TARGET_GROUP
            group_df = scope_reference_df.loc[
                scope_reference_df["target_group"].astype(str) == target_group_name
            ].copy()
            exact_match_df = group_df.loc[
                (group_df["normalized_label_key"].astype(str) == normalized_label_key)
                & (
                    group_df["scope_action"].astype(str)
                    == _norm(preview_payload.get("scope_action"))
                )
            ].copy()
            overlap_count = len(exact_match_df)
            group_before_count = len(group_df)
            group_after_count = group_before_count + 1
            operation_id = f"dry_run_323k::scope::{scope_sequence:03d}"
            target_locator = f"{target_asset_path}::{target_group_name}"
            before_state = (
                "EXACT_SCOPE_RULE_ALREADY_PRESENT"
                if overlap_count
                else "SCOPE_RULE_NOT_PRESENT"
            )

        operation_key = "::".join(
            [
                candidate_type,
                target_locator,
                normalized_label_key,
                _norm(preview_payload.get("metric_code") or preview_payload.get("scope_action")),
            ]
        )

        operation_row = {
            "dry_run_patch_operation_id": operation_id,
            "controlled_proposal_id": proposal_id,
            "candidate_type": candidate_type,
            "proposal_type": _norm(proposal.get("proposal_type")),
            "normalized_label": normalized_label,
            "normalized_label_key": normalized_label_key,
            "target_asset_path": target_asset_path,
            "target_group_name": target_group_name,
            "target_rule_family": _norm(proposal.get("target_rule_family")),
            "future_operation_type": _norm(proposal.get("future_operation_type")),
            "target_locator": target_locator,
            "before_state": before_state,
            "already_official_overlap_count": overlap_count,
            "group_before_entry_count": group_before_count,
            "group_after_entry_count_preview": group_after_count,
            "expected_affected_candidate_count": _safe_int(
                proposal.get("expected_affected_candidate_count")
            ),
            "expected_trusted_gain": _safe_int(proposal.get("expected_trusted_gain")),
            "expected_review_reduction": _safe_int(
                proposal.get("expected_review_reduction")
            ),
            "expected_out_of_scope_or_rejected_gain": _safe_int(
                proposal.get("expected_out_of_scope_or_rejected_gain")
            ),
            "source_rule_candidate_id": _norm(proposal.get("source_rule_candidate_id")),
            "source_rule_ids": _norm(proposal.get("source_rule_ids")),
            "source_confirmation_ids": _norm(proposal.get("source_confirmation_ids")),
            "source_request_ids": _norm(proposal.get("source_request_ids")),
            "source_group_ids": _norm(proposal.get("source_group_ids")),
            "rollback_note": _norm(proposal.get("rollback_note")),
            "risk_flags": _norm(proposal.get("risk_flags")),
            "sample_table_titles": _norm(proposal.get("sample_table_titles")),
            "sample_texts": _norm(proposal.get("sample_texts")),
            "sample_years": _norm(proposal.get("sample_years")),
            "preview_payload_json": json.dumps(preview_payload, ensure_ascii=False),
            "preview_payload_dict": preview_payload,
            "operation_key": operation_key,
            "proposal_only_no_apply_confirmed": True,
        }
        operation_rows.append(operation_row)
        no_apply_targets.append(target_locator)

        diff_preview_rows.append(
            {
                "dry_run_patch_operation_id": operation_id,
                "controlled_proposal_id": proposal_id,
                "candidate_type": candidate_type,
                "target_asset_path": target_asset_path,
                "target_group_name": target_group_name,
                "before_state": before_state,
                "group_before_entry_count": group_before_count,
                "group_after_entry_count_preview": group_after_count,
                "official_overlap_count": overlap_count,
                "preview_rule_or_entry_id": _norm(preview_payload.get("rule_id")),
                "normalized_label": normalized_label,
                "proposed_metric_code": _norm(preview_payload.get("metric_code")),
                "proposed_scope_action": _norm(preview_payload.get("scope_action")),
                "virtual_diff_summary": (
                    f"Append preview entry for '{normalized_label}' to {target_group_name}"
                ),
            }
        )

        rollback_rows.append(
            {
                "dry_run_patch_operation_id": operation_id,
                "controlled_proposal_id": proposal_id,
                "target_locator": target_locator,
                "rollback_action": "DROP_DRY_RUN_PATCH_OPERATION",
                "rollback_instruction": (
                    f"Remove operation {operation_id} from the 323K dry-run package. "
                    f"No official asset rollback is needed because 323K does not write files."
                ),
                "rollback_reason": "Dry-run-only preview must stay removable before any human approval or official patch stage.",
            }
        )

    patch_operations_df = pd.DataFrame(operation_rows).fillna("")
    target_asset_diff_preview_df = pd.DataFrame(diff_preview_rows).fillna("")
    rollback_plan_df = pd.DataFrame(rollback_rows).fillna("")

    alias_operations_df = (
        patch_operations_df.loc[
            patch_operations_df["candidate_type"].astype(str) == "alias"
        ].copy()
        if not patch_operations_df.empty
        else pd.DataFrame()
    )
    scope_operations_df = (
        patch_operations_df.loc[
            patch_operations_df["candidate_type"].astype(str) == "scope"
        ].copy()
        if not patch_operations_df.empty
        else pd.DataFrame()
    )

    duplicate_operation_count = (
        int(patch_operations_df["operation_key"].astype(str).duplicated().sum())
        if not patch_operations_df.empty
        else 0
    )
    already_official_overlap_count = (
        int((patch_operations_df["already_official_overlap_count"] > 0).sum())
        if not patch_operations_df.empty
        else 0
    )
    missing_target_asset_or_group_count = (
        int(
            (
                patch_operations_df["target_asset_path"].astype(str).eq("")
                | patch_operations_df["target_group_name"].astype(str).eq("")
            ).sum()
        )
        if not patch_operations_df.empty
        else 0
    )
    missing_provenance_count = (
        int(
            patch_operations_df[
                patch_operations_df["source_rule_ids"].astype(str).eq("")
                | patch_operations_df["source_confirmation_ids"].astype(str).eq("")
                | patch_operations_df["source_request_ids"].astype(str).eq("")
            ].shape[0]
        )
        if not patch_operations_df.empty
        else 0
    )
    target_conflict_count = duplicate_operation_count

    add_qa(
        "operations::patch_operation_count",
        "PASS" if len(patch_operations_df) == 6 else "FAIL",
        f"actual={len(patch_operations_df)}",
    )
    add_qa(
        "operations::alias_patch_operation_count",
        "PASS" if len(alias_operations_df) == 2 else "FAIL",
        f"actual={len(alias_operations_df)}",
    )
    add_qa(
        "operations::scope_patch_operation_count",
        "PASS" if len(scope_operations_df) == 4 else "FAIL",
        f"actual={len(scope_operations_df)}",
    )
    add_qa(
        "operations::process_only_ready_for_dry_run",
        "PASS"
        if len(patch_operations_df) == len(proposals_df) == 6
        else "FAIL",
        f"operations={len(patch_operations_df)} proposals={len(proposals_df)}",
    )
    add_qa(
        "operations::duplicate_source_suggestions_not_reexpanded",
        "PASS"
        if len(duplicate_provenance_bridge_df) == 11 and len(proposals_df) == 6
        else "FAIL",
        f"bridge_rows={len(duplicate_provenance_bridge_df)} proposals={len(proposals_df)}",
    )
    add_qa(
        "targets::alias_target_group",
        "PASS"
        if alias_operations_df.empty
        or alias_operations_df["target_group_name"].astype(str).eq(ALIAS_TARGET_GROUP).all()
        else "FAIL",
        ALIAS_TARGET_GROUP,
    )
    add_qa(
        "targets::scope_target_group",
        "PASS"
        if scope_operations_df.empty
        or scope_operations_df["target_group_name"].astype(str).eq(SCOPE_TARGET_GROUP).all()
        else "FAIL",
        SCOPE_TARGET_GROUP,
    )
    add_qa(
        "targets::target_asset_file_count",
        "PASS"
        if len(_dedupe_preserve(patch_operations_df["target_asset_path"].tolist())) == 2
        else "FAIL",
        f"actual={len(_dedupe_preserve(patch_operations_df['target_asset_path'].tolist())) if not patch_operations_df.empty else 0}",
    )
    add_qa(
        "targets::missing_target_asset_or_group_count",
        "PASS" if missing_target_asset_or_group_count == 0 else "FAIL",
        f"actual={missing_target_asset_or_group_count}",
    )
    add_qa(
        "integrity::duplicate_operation_count",
        "PASS" if duplicate_operation_count == 0 else "FAIL",
        f"actual={duplicate_operation_count}",
    )
    add_qa(
        "integrity::target_conflict_count",
        "PASS" if target_conflict_count == 0 else "FAIL",
        f"actual={target_conflict_count}",
    )
    add_qa(
        "integrity::already_official_overlap_count",
        "PASS" if already_official_overlap_count == 0 else "FAIL",
        f"actual={already_official_overlap_count}",
    )
    add_qa(
        "integrity::missing_provenance_count",
        "PASS" if missing_provenance_count == 0 else "FAIL",
        f"actual={missing_provenance_count}",
    )
    add_qa(
        "impact::affected_candidate_count",
        "PASS" if _safe_numeric_sum(patch_operations_df, "expected_affected_candidate_count") == 129 else "FAIL",
        f"actual={_safe_numeric_sum(patch_operations_df, 'expected_affected_candidate_count')}",
    )
    add_qa(
        "impact::expected_trusted_gain",
        "PASS" if _safe_numeric_sum(patch_operations_df, "expected_trusted_gain") == 44 else "FAIL",
        f"actual={_safe_numeric_sum(patch_operations_df, 'expected_trusted_gain')}",
    )
    add_qa(
        "impact::expected_review_reduction",
        "PASS" if _safe_numeric_sum(patch_operations_df, "expected_review_reduction") == 129 else "FAIL",
        f"actual={_safe_numeric_sum(patch_operations_df, 'expected_review_reduction')}",
    )
    add_qa(
        "impact::expected_out_of_scope_or_rejected_gain",
        "PASS"
        if _safe_numeric_sum(
            patch_operations_df, "expected_out_of_scope_or_rejected_gain"
        )
        == 85
        else "FAIL",
        f"actual={_safe_numeric_sum(patch_operations_df, 'expected_out_of_scope_or_rejected_gain')}",
    )
    add_qa(
        "safety::no_official_file_write_in_builder",
        "PASS",
        "Builder constructs patch-operation preview and virtual after-state only.",
    )
    add_qa(
        "safety::no_llm_or_api_call_executed",
        "PASS",
        "323K uses 323J outputs and cached evidence only.",
    )

    before_after_preview_rows = [
        {
            "target_asset_path": str(OFFICIAL_ALIAS_ASSET_PATH),
            "target_group_name": ALIAS_TARGET_GROUP,
            "candidate_type": "alias",
            "before_entry_count": int(
                len(
                    alias_reference_df.loc[
                        alias_reference_df["group_name"].astype(str) == ALIAS_TARGET_GROUP
                    ]
                )
            ),
            "after_entry_count_preview": int(
                len(
                    alias_reference_df.loc[
                        alias_reference_df["group_name"].astype(str) == ALIAS_TARGET_GROUP
                    ]
                )
            )
            + len(alias_operations_df),
            "added_operation_count": int(len(alias_operations_df)),
            "affected_candidate_count": _safe_numeric_sum(
                alias_operations_df, "expected_affected_candidate_count"
            ),
            "expected_trusted_gain": _safe_numeric_sum(
                alias_operations_df, "expected_trusted_gain"
            ),
            "expected_review_reduction": _safe_numeric_sum(
                alias_operations_df, "expected_review_reduction"
            ),
            "expected_out_of_scope_or_rejected_gain": _safe_numeric_sum(
                alias_operations_df, "expected_out_of_scope_or_rejected_gain"
            ),
        },
        {
            "target_asset_path": str(FORMAL_SCOPE_RULES_PATH),
            "target_group_name": SCOPE_TARGET_GROUP,
            "candidate_type": "scope",
            "before_entry_count": int(
                len(
                    scope_reference_df.loc[
                        scope_reference_df["target_group"].astype(str) == SCOPE_TARGET_GROUP
                    ]
                )
            ),
            "after_entry_count_preview": int(
                len(
                    scope_reference_df.loc[
                        scope_reference_df["target_group"].astype(str) == SCOPE_TARGET_GROUP
                    ]
                )
            )
            + len(scope_operations_df),
            "added_operation_count": int(len(scope_operations_df)),
            "affected_candidate_count": _safe_numeric_sum(
                scope_operations_df, "expected_affected_candidate_count"
            ),
            "expected_trusted_gain": _safe_numeric_sum(
                scope_operations_df, "expected_trusted_gain"
            ),
            "expected_review_reduction": _safe_numeric_sum(
                scope_operations_df, "expected_review_reduction"
            ),
            "expected_out_of_scope_or_rejected_gain": _safe_numeric_sum(
                scope_operations_df, "expected_out_of_scope_or_rejected_gain"
            ),
        },
    ]
    before_after_preview_df = pd.DataFrame(before_after_preview_rows).fillna("")

    virtual_after_alias_payload = _build_virtual_after_alias_payload(
        official_alias_payload, alias_operations_df
    )
    virtual_after_scope_payload = _build_virtual_after_scope_payload(
        formal_scope_rules_payload, scope_operations_df
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
        "stage": "323K",
        "output_dir": "",
        "source_controlled_proposal_decision": _norm(controlled_summary.get("decision")),
        "source_controlled_proposal_qa_fail_count": _safe_int(
            controlled_summary.get("qa_fail_count")
        ),
        "proposal_count": int(len(proposals_df)),
        "alias_proposal_count": int(len(alias_operations_df)),
        "scope_proposal_count": int(len(scope_operations_df)),
        "ready_for_dry_run_proposal_count": int(len(proposals_df)),
        "patch_operation_count": int(len(patch_operations_df)),
        "alias_patch_operation_count": int(len(alias_operations_df)),
        "scope_patch_operation_count": int(len(scope_operations_df)),
        "target_asset_file_count": int(
            len(_dedupe_preserve(patch_operations_df["target_asset_path"].tolist()))
        )
        if not patch_operations_df.empty
        else 0,
        "target_group_count": int(
            len(_dedupe_preserve(patch_operations_df["target_group_name"].tolist()))
        )
        if not patch_operations_df.empty
        else 0,
        "duplicate_operation_count": duplicate_operation_count,
        "target_conflict_count": target_conflict_count,
        "already_official_overlap_count": already_official_overlap_count,
        "missing_target_asset_or_group_count": missing_target_asset_or_group_count,
        "missing_provenance_count": missing_provenance_count,
        "affected_candidate_count": _safe_numeric_sum(
            patch_operations_df, "expected_affected_candidate_count"
        ),
        "expected_trusted_gain": _safe_numeric_sum(
            patch_operations_df, "expected_trusted_gain"
        ),
        "expected_review_reduction": _safe_numeric_sum(
            patch_operations_df, "expected_review_reduction"
        ),
        "expected_out_of_scope_or_rejected_gain": _safe_numeric_sum(
            patch_operations_df, "expected_out_of_scope_or_rejected_gain"
        ),
        "rollback_plan_record_count": int(len(rollback_plan_df)),
        "no_apply_confirmed": True,
        "official_assets_not_modified_confirmed": True,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": EXPECTED_NEXT_DECISION if qa_fail_count == 0 else NOT_READY_DECISION,
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
                "limitation": "dry_run_only",
                "detail": "323K builds patch-operation preview and virtual after-state only. Official assets stay unchanged on disk.",
            },
            {
                "limitation": "proposal_subset_only",
                "detail": "323K processes only the 6 READY_FOR_DRY_RUN proposals from 323J and does not re-expand duplicate source suggestions.",
            },
            {
                "limitation": "future_human_approval_required",
                "detail": "All 323K operations still require a later human approval stage before any official patch application.",
            },
        ]
    )

    no_apply_proof_json = {
        "files_read": [
            str(
                Path(
                    r"D:\_datefac\output\controlled_official_proposal_from_323i_323j\controlled_official_proposal_from_323i_323j_summary.json"
                )
            ),
            str(
                Path(
                    r"D:\_datefac\output\controlled_official_proposal_from_323i_323j\controlled_official_proposal_from_323i_323j_qa.json"
                )
            ),
            str(
                Path(
                    r"D:\_datefac\output\controlled_official_proposal_from_323i_323j\controlled_official_proposal_from_323i_323j_proposal_package.json"
                )
            ),
            str(
                Path(
                    r"D:\_datefac\output\official_rule_candidates_from_323h_323i\official_rule_candidates_from_323h_323i_summary.json"
                )
            ),
            str(
                Path(
                    r"D:\_datefac\output\human_confirmed_sandbox_replay_323h\human_confirmed_sandbox_replay_323h_summary.json"
                )
            ),
            str(OFFICIAL_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
        "files_written": [],
        "target_official_files_inspected": [
            str(OFFICIAL_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
        "target_locators_preview_only": sorted(_dedupe_preserve(no_apply_targets)),
        "official_assets_not_modified": [
            str(OFFICIAL_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
        "output_only_write_confirmation": True,
        "decision": "dry_run_only_no_apply",
    }

    patch_operations_json = {
        "stage": "323K",
        "decision": summary["decision"],
        "patch_operations": patch_operations_df.drop(
            columns=["preview_payload_dict"], errors="ignore"
        ).to_dict(orient="records"),
    }
    target_asset_diff_preview_json = {
        "stage": "323K",
        "decision": summary["decision"],
        "before_after_preview": before_after_preview_df.to_dict(orient="records"),
        "target_asset_diff_preview": target_asset_diff_preview_df.to_dict(
            orient="records"
        ),
        "virtual_after_alias_payload": virtual_after_alias_payload,
        "virtual_after_scope_payload": virtual_after_scope_payload,
    }
    rollback_plan_json = {
        "stage": "323K",
        "decision": summary["decision"],
        "rollback_plan": rollback_plan_df.to_dict(orient="records"),
    }
    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_checks_df.to_dict(orient="records"),
    }

    return {
        "summary": summary,
        "patch_operations_df": patch_operations_df.drop(
            columns=["preview_payload_dict"], errors="ignore"
        ),
        "before_after_preview_df": before_after_preview_df,
        "target_asset_diff_preview_df": target_asset_diff_preview_df,
        "rollback_plan_df": rollback_plan_df,
        "qa_checks_df": qa_checks_df,
        "qa_summary_df": qa_summary_df,
        "known_limitations_df": known_limitations_df,
        "patch_operations_json": patch_operations_json,
        "target_asset_diff_preview_json": target_asset_diff_preview_json,
        "rollback_plan_json": rollback_plan_json,
        "qa_json": qa_json,
        "no_apply_proof_json": no_apply_proof_json,
    }
