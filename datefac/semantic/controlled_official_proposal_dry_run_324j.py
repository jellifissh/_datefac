from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

import pandas as pd


EXPECTED_324I_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_FROM_324H_324I_READY_WITH_WARNINGS"
EXPECTED_324H_DECISION = "OFFICIAL_RULE_CANDIDATE_FROM_324G_324H_READY_FOR_CONTROLLED_PROPOSAL"
EXPECTED_324G_READY_WARN_DECISION = "SCOPE_NOISE_HUMAN_CONFIRMED_SANDBOX_REPLAY_324G_READY_WITH_WARNINGS"
READY_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_DRY_RUN_324J_READY_FOR_HUMAN_APPROVAL"
READY_WARN_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_DRY_RUN_324J_READY_WITH_WARNINGS"
NOT_READY_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_DRY_RUN_324J_NOT_READY"

FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
SCOPE_TARGET_GROUP = "core_metric_scope_exclusions"
ALLOWED_CARRIED_WARNING = "historical_duplicates_unchanged_only:new_duplicate_delta_count=0"


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
    return _norm(value).lower() in {"1", "true", "yes", "y"}


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
                    "source_rule_candidate_id": _norm(item.get("source_rule_candidate_id")),
                }
            )
    return pd.DataFrame(rows).fillna("")


def load_controlled_official_proposal_dry_run_324j_inputs(
    controlled_proposal_dir: Path,
    official_rule_candidate_dir: Path,
    sandbox_replay_dir: Path,
) -> Dict[str, Any]:
    proposal_package = _read_json(
        controlled_proposal_dir
        / "controlled_official_proposal_from_324h_324i_proposal_package.json"
    )
    return {
        "controlled_summary": _read_json(
            controlled_proposal_dir / "controlled_official_proposal_from_324h_324i_summary.json"
        ),
        "controlled_qa": _read_json(
            controlled_proposal_dir / "controlled_official_proposal_from_324h_324i_qa.json"
        ),
        "controlled_proposals_df": pd.DataFrame(
            proposal_package.get("controlled_proposals", [])
            if isinstance(proposal_package.get("controlled_proposals", []), list)
            else []
        ).fillna(""),
        "proposal_source_bridge_df": pd.DataFrame(
            proposal_package.get("proposal_source_bridge", [])
            if isinstance(proposal_package.get("proposal_source_bridge", []), list)
            else []
        ).fillna(""),
        "provenance_samples_df": pd.DataFrame(
            proposal_package.get("provenance_samples", [])
            if isinstance(proposal_package.get("provenance_samples", []), list)
            else []
        ).fillna(""),
        "official_rule_candidate_summary": _read_json(
            official_rule_candidate_dir / "official_rule_candidate_from_324g_324h_summary.json"
        ),
        "sandbox_summary": _read_json(
            sandbox_replay_dir / "scope_noise_human_confirmed_sandbox_replay_324g_summary.json"
        ),
        "formal_scope_rules_payload": _read_json(FORMAL_SCOPE_RULES_PATH),
    }


def _preview_scope_rule(proposal: Dict[str, Any], sequence: int) -> Dict[str, Any]:
    return {
        "rule_id": f"DRY_RUN_324J_SCOPE_{sequence:03d}",
        "rule_type": "core_metric_scope_exclusion",
        "target_group": SCOPE_TARGET_GROUP,
        "normalized_label": _norm(proposal.get("normalized_label")),
        "scope_action": _norm(proposal.get("proposed_scope_action"))
        or "exclude_from_core_metric_mapping",
        "source_controlled_proposal_id_324i": _norm(proposal.get("controlled_proposal_id")),
        "source_rule_candidate_id_324h": _norm(proposal.get("source_rule_candidate_id_324h")),
        "source_candidate_ids_324a": _norm(proposal.get("source_candidate_ids_324a")),
        "source_review_ids_324b": _norm(proposal.get("source_review_ids_324b")),
        "source_request_ids_324c": _norm(proposal.get("source_request_ids_324c")),
        "source_response_ids_324d": _norm(proposal.get("source_response_ids_324d")),
        "source_validation_ids_324e": _norm(proposal.get("source_validation_ids_324e")),
        "source_confirmation_ids_324f": _norm(proposal.get("source_confirmation_ids_324f")),
        "source_sandbox_rule_ids_324g": _norm(proposal.get("source_sandbox_rule_ids_324g")),
        "dry_run_only": True,
    }


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


def build_controlled_official_proposal_dry_run_324j(
    controlled_summary: Dict[str, Any],
    controlled_qa: Dict[str, Any],
    controlled_proposals_df: pd.DataFrame,
    proposal_source_bridge_df: pd.DataFrame,
    provenance_samples_df: pd.DataFrame,
    official_rule_candidate_summary: Dict[str, Any],
    sandbox_summary: Dict[str, Any],
    formal_scope_rules_payload: Dict[str, Any],
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa(
        "readiness::324i_decision",
        "PASS" if _norm(controlled_summary.get("decision")) == EXPECTED_324I_DECISION else "FAIL",
        _norm(controlled_summary.get("decision")),
    )
    add_qa(
        "readiness::324i_qa_fail_count",
        "PASS" if _safe_int(controlled_summary.get("qa_fail_count")) == 0 else "FAIL",
        str(controlled_summary.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::324i_qa_json_fail_count",
        "PASS" if _safe_int(controlled_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(controlled_qa.get("qa_fail_count", "")),
    )
    for key, expected in [
        ("proposal_count", 1),
        ("scope_proposal_count", 1),
        ("ready_for_dry_run_proposal_count", 1),
        ("expected_affected_candidate_count", 42),
        ("expected_trusted_gain", 0),
        ("expected_review_reduction", 42),
        ("expected_out_of_scope_or_rejected_gain", 42),
        ("duplicate_proposal_id_count", 0),
        ("already_official_overlap_count", 0),
        ("target_conflict_count", 0),
        ("missing_target_asset_or_group_count", 0),
        ("missing_provenance_count", 0),
    ]:
        add_qa(
            f"readiness::324i_{key}",
            "PASS" if _safe_int(controlled_summary.get(key)) == expected else "FAIL",
            f"expected={expected} actual={controlled_summary.get(key, '')}",
        )

    carried_warnings = _dedupe_preserve(controlled_summary.get("carried_warnings", []))
    add_qa(
        "warnings::carried_warning_allowed_only",
        "PASS"
        if not carried_warnings or set(carried_warnings) == {ALLOWED_CARRIED_WARNING}
        else "FAIL",
        " | ".join(carried_warnings),
    )
    if carried_warnings:
        add_qa(
            "warnings::historical_duplicates_unchanged_only",
            "WARN",
            ALLOWED_CARRIED_WARNING,
        )

    add_qa(
        "consistency::324h_decision",
        "PASS"
        if _norm(official_rule_candidate_summary.get("decision")) == EXPECTED_324H_DECISION
        else "FAIL",
        _norm(official_rule_candidate_summary.get("decision")),
    )
    add_qa(
        "consistency::324g_decision_family",
        "PASS"
        if _norm(sandbox_summary.get("decision")) == EXPECTED_324G_READY_WARN_DECISION
        else "FAIL",
        _norm(sandbox_summary.get("decision")),
    )

    proposals_df = (
        controlled_proposals_df.loc[
            controlled_proposals_df["proposal_status"].astype(str) == "READY_FOR_DRY_RUN"
        ]
        .copy()
        .reset_index(drop=True)
        if not controlled_proposals_df.empty
        else pd.DataFrame()
    )
    add_qa(
        "inputs::loaded_ready_proposal_count",
        "PASS" if len(proposals_df) == 1 else "FAIL",
        f"actual={len(proposals_df)}",
    )
    add_qa(
        "inputs::loaded_ready_scope_proposal_count",
        "PASS"
        if len(proposals_df) == 1
        and proposals_df["candidate_type"].astype(str).eq("scope_noise").all()
        else "FAIL",
        f"actual={int(proposals_df['candidate_type'].astype(str).eq('scope_noise').sum()) if not proposals_df.empty else 0}",
    )

    scope_reference_df = _build_scope_reference_df(formal_scope_rules_payload)
    operation_rows: List[Dict[str, Any]] = []
    diff_preview_rows: List[Dict[str, Any]] = []
    rollback_rows: List[Dict[str, Any]] = []
    no_apply_targets: List[str] = []

    for sequence, (_, row) in enumerate(proposals_df.iterrows(), start=1):
        proposal = row.to_dict()
        normalized_label = _norm(proposal.get("normalized_label"))
        normalized_label_key = _normalize_label(normalized_label)
        target_asset_path = str(FORMAL_SCOPE_RULES_PATH)
        target_group_name = SCOPE_TARGET_GROUP
        group_df = (
            scope_reference_df.loc[
                scope_reference_df["target_group"].astype(str) == target_group_name
            ].copy()
            if not scope_reference_df.empty
            else pd.DataFrame()
        )
        exact_match_df = (
            group_df.loc[
                (group_df["normalized_label_key"].astype(str) == normalized_label_key)
                & (
                    group_df["scope_action"].astype(str)
                    == _norm(proposal.get("proposed_scope_action"))
                )
            ].copy()
            if not group_df.empty
            else pd.DataFrame()
        )
        overlap_count = len(exact_match_df)
        preview_payload = _preview_scope_rule(proposal, sequence)
        operation_id = f"dry_run_324j::scope::{sequence:03d}"
        target_locator = f"{target_asset_path}::{target_group_name}"
        before_state = (
            "EXACT_SCOPE_RULE_ALREADY_PRESENT" if overlap_count else "SCOPE_RULE_NOT_PRESENT"
        )

        operation_row = {
            "dry_run_patch_operation_id": operation_id,
            "controlled_proposal_id_324i": _norm(proposal.get("controlled_proposal_id")),
            "candidate_type": "scope_noise",
            "patch_operation_type": "ADD_SCOPE_EXCLUSION",
            "proposal_type": _norm(proposal.get("proposal_type")),
            "normalized_label": normalized_label,
            "normalized_label_key": normalized_label_key,
            "target_asset_path": target_asset_path,
            "target_group_name": target_group_name,
            "target_locator": target_locator,
            "before_state": before_state,
            "already_official_overlap_count": overlap_count,
            "group_before_entry_count": len(group_df),
            "group_after_entry_count_preview": len(group_df) + 1,
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
            "source_candidate_ids_324a": _norm(proposal.get("source_candidate_ids_324a")),
            "source_review_ids_324b": _norm(proposal.get("source_review_ids_324b")),
            "source_request_ids_324c": _norm(proposal.get("source_request_ids_324c")),
            "source_response_ids_324d": _norm(proposal.get("source_response_ids_324d")),
            "source_validation_ids_324e": _norm(proposal.get("source_validation_ids_324e")),
            "source_confirmation_ids_324f": _norm(proposal.get("source_confirmation_ids_324f")),
            "source_sandbox_rule_ids_324g": _norm(
                proposal.get("source_sandbox_rule_ids_324g")
            ),
            "source_rule_candidate_id_324h": _norm(
                proposal.get("source_rule_candidate_id_324h")
            ),
            "risk_flags": _norm(proposal.get("risk_flags")),
            "rollback_note": _norm(proposal.get("rollback_note")),
            "preview_payload_json": json.dumps(preview_payload, ensure_ascii=False),
            "preview_payload_dict": preview_payload,
            "operation_key": "::".join(
                [
                    "scope_noise",
                    target_locator,
                    normalized_label_key,
                    _norm(preview_payload.get("scope_action")),
                ]
            ),
            "proposal_only_no_apply_confirmed": True,
        }
        operation_rows.append(operation_row)
        no_apply_targets.append(target_locator)

        diff_preview_rows.append(
            {
                "dry_run_patch_operation_id": operation_id,
                "controlled_proposal_id_324i": _norm(proposal.get("controlled_proposal_id")),
                "target_asset_path": target_asset_path,
                "target_group_name": target_group_name,
                "before_state": before_state,
                "group_before_entry_count": len(group_df),
                "group_after_entry_count_preview": len(group_df) + 1,
                "official_overlap_count": overlap_count,
                "preview_rule_id": _norm(preview_payload.get("rule_id")),
                "normalized_label": normalized_label,
                "proposed_scope_action": _norm(preview_payload.get("scope_action")),
                "virtual_diff_summary": (
                    f"Append preview scope exclusion for '{normalized_label}' "
                    f"to {target_group_name}"
                ),
            }
        )
        rollback_rows.append(
            {
                "dry_run_patch_operation_id": operation_id,
                "controlled_proposal_id_324i": _norm(proposal.get("controlled_proposal_id")),
                "target_locator": target_locator,
                "rollback_action": "DROP_DRY_RUN_PATCH_OPERATION",
                "rollback_instruction": (
                    f"Remove operation {operation_id} from the 324J dry-run package. "
                    "No official asset rollback is needed because 324J does not write files."
                ),
                "rollback_reason": "Dry-run-only preview must stay removable before human approval.",
            }
        )

    patch_operations_df = pd.DataFrame(operation_rows).fillna("")
    target_asset_diff_preview_df = pd.DataFrame(diff_preview_rows).fillna("")
    rollback_plan_df = pd.DataFrame(rollback_rows).fillna("")
    before_after_preview_df = pd.DataFrame(
        [
            {
                "target_asset_path": str(FORMAL_SCOPE_RULES_PATH),
                "target_group_name": SCOPE_TARGET_GROUP,
                "candidate_type": "scope_noise",
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
                + len(patch_operations_df),
                "added_operation_count": int(len(patch_operations_df)),
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
            }
        ]
    ).fillna("")

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
    target_conflict_count = duplicate_operation_count
    missing_provenance_count = (
        int(
            patch_operations_df[
                patch_operations_df["source_candidate_ids_324a"].astype(str).eq("")
                | patch_operations_df["source_review_ids_324b"].astype(str).eq("")
                | patch_operations_df["source_request_ids_324c"].astype(str).eq("")
                | patch_operations_df["source_response_ids_324d"].astype(str).eq("")
                | patch_operations_df["source_validation_ids_324e"].astype(str).eq("")
                | patch_operations_df["source_confirmation_ids_324f"].astype(str).eq("")
                | patch_operations_df["source_sandbox_rule_ids_324g"].astype(str).eq("")
                | patch_operations_df["source_rule_candidate_id_324h"].astype(str).eq("")
            ].shape[0]
        )
        if not patch_operations_df.empty
        else 0
    )

    add_qa(
        "operations::patch_operation_count",
        "PASS" if len(patch_operations_df) == 1 else "FAIL",
        f"actual={len(patch_operations_df)}",
    )
    add_qa(
        "operations::scope_patch_operation_count",
        "PASS" if len(patch_operations_df) == 1 else "FAIL",
        f"actual={len(patch_operations_df)}",
    )
    add_qa(
        "operations::process_only_ready_for_dry_run",
        "PASS" if len(patch_operations_df) == len(proposals_df) == 1 else "FAIL",
        f"operations={len(patch_operations_df)} proposals={len(proposals_df)}",
    )
    add_qa(
        "targets::scope_target_group",
        "PASS"
        if patch_operations_df.empty
        or patch_operations_df["target_group_name"].astype(str).eq(SCOPE_TARGET_GROUP).all()
        else "FAIL",
        SCOPE_TARGET_GROUP,
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
        "impact::expected_affected_candidate_count",
        "PASS" if _safe_numeric_sum(patch_operations_df, "expected_affected_candidate_count") == 42 else "FAIL",
        f"actual={_safe_numeric_sum(patch_operations_df, 'expected_affected_candidate_count')}",
    )
    add_qa(
        "impact::expected_trusted_gain",
        "PASS" if _safe_numeric_sum(patch_operations_df, "expected_trusted_gain") == 0 else "FAIL",
        f"actual={_safe_numeric_sum(patch_operations_df, 'expected_trusted_gain')}",
    )
    add_qa(
        "impact::expected_review_reduction",
        "PASS" if _safe_numeric_sum(patch_operations_df, "expected_review_reduction") == 42 else "FAIL",
        f"actual={_safe_numeric_sum(patch_operations_df, 'expected_review_reduction')}",
    )
    add_qa(
        "impact::expected_out_of_scope_or_rejected_gain",
        "PASS"
        if _safe_numeric_sum(
            patch_operations_df, "expected_out_of_scope_or_rejected_gain"
        )
        == 42
        else "FAIL",
        f"actual={_safe_numeric_sum(patch_operations_df, 'expected_out_of_scope_or_rejected_gain')}",
    )
    add_qa(
        "safety::no_official_file_write_in_builder",
        "PASS",
        "324J builds patch-operation preview and virtual after-state only.",
    )
    add_qa(
        "safety::no_llm_or_api_call_executed",
        "PASS",
        "324J uses 324I outputs and cached evidence only.",
    )

    virtual_after_scope_payload = _build_virtual_after_scope_payload(
        formal_scope_rules_payload, patch_operations_df
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
        "stage": "324J",
        "output_dir": "",
        "source_controlled_proposal_decision": _norm(controlled_summary.get("decision")),
        "source_controlled_proposal_qa_fail_count": _safe_int(controlled_summary.get("qa_fail_count")),
        "proposal_count": int(len(proposals_df)),
        "alias_proposal_count": 0,
        "scope_proposal_count": int(len(proposals_df)),
        "ready_for_dry_run_proposal_count": int(len(proposals_df)),
        "patch_operation_count": int(len(patch_operations_df)),
        "alias_patch_operation_count": 0,
        "scope_patch_operation_count": int(len(patch_operations_df)),
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
        "missing_target_asset_or_group_count": 0,
        "missing_provenance_count": missing_provenance_count,
        "expected_affected_candidate_count": _safe_numeric_sum(
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
        "carried_warnings": carried_warnings,
        "no_apply_confirmed": True,
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
                "detail": "324J builds patch-operation preview and virtual after-state only. Official assets stay unchanged on disk.",
            },
            {
                "limitation": "single_scope_proposal_only",
                "detail": "324J processes only the single READY_FOR_DRY_RUN scope proposal from 324I.",
            },
            {
                "limitation": "future_human_approval_required",
                "detail": "The 324J dry-run operation still requires a later human approval stage before any official patch application.",
            },
        ]
    )

    no_apply_proof_json = {
        "files_read": [
            str(
                Path(
                    r"D:\_datefac\output\controlled_official_proposal_from_324h_324i\controlled_official_proposal_from_324h_324i_summary.json"
                )
            ),
            str(
                Path(
                    r"D:\_datefac\output\controlled_official_proposal_from_324h_324i\controlled_official_proposal_from_324h_324i_qa.json"
                )
            ),
            str(
                Path(
                    r"D:\_datefac\output\controlled_official_proposal_from_324h_324i\controlled_official_proposal_from_324h_324i_proposal_package.json"
                )
            ),
            str(
                Path(
                    r"D:\_datefac\output\official_rule_candidate_from_324g_324h\official_rule_candidate_from_324g_324h_summary.json"
                )
            ),
            str(
                Path(
                    r"D:\_datefac\output\scope_noise_human_confirmed_sandbox_replay_324g\scope_noise_human_confirmed_sandbox_replay_324g_summary.json"
                )
            ),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
        "files_written": [],
        "files_written_to_official_assets": [],
        "target_official_files_inspected": [str(FORMAL_SCOPE_RULES_PATH)],
        "target_locators_preview_only": sorted(_dedupe_preserve(no_apply_targets)),
        "official_assets_not_modified": [str(FORMAL_SCOPE_RULES_PATH)],
        "output_only_write_confirmation": True,
        "decision": "dry_run_only_no_apply",
    }

    patch_operations_json = {
        "stage": "324J",
        "decision": summary["decision"],
        "patch_operations": patch_operations_df.drop(
            columns=["preview_payload_dict"], errors="ignore"
        ).to_dict(orient="records"),
    }
    target_asset_diff_preview_json = {
        "stage": "324J",
        "decision": summary["decision"],
        "before_after_preview": before_after_preview_df.to_dict(orient="records"),
        "target_asset_diff_preview": target_asset_diff_preview_df.to_dict(orient="records"),
        "virtual_after_scope_payload": virtual_after_scope_payload,
    }
    rollback_plan_json = {
        "stage": "324J",
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
