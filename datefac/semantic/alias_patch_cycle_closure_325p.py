from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


EXPECTED_325O_DECISION = "POST_PATCH_REGRESSION_VALIDATION_325O_READY_FOR_325P_CYCLE_CLOSURE"
READY_DECISION = "ALIAS_PATCH_CYCLE_325P_CLOSED_READY_FOR_TRUST_ENGINE_CONSOLIDATION"
READY_WITH_WARNINGS_DECISION = "ALIAS_PATCH_CYCLE_325P_CLOSED_WITH_WARNINGS_READY_FOR_TRUST_ENGINE_CONSOLIDATION"
NOT_READY_DECISION = "ALIAS_PATCH_CYCLE_325P_NOT_READY"

DEFAULT_POST_PATCH_REGRESSION_DIR = Path(r"D:\_datefac\output\post_patch_regression_validation_325o")
DEFAULT_OFFICIAL_PATCH_APPLICATION_DIR = Path(r"D:\_datefac\output\official_alias_patch_application_325n")
DEFAULT_PREVIOUS_CYCLE_CLOSURE_DIR = Path(r"D:\_datefac\output\official_scope_patch_cycle_closure_324n")
DEFAULT_REMAINING_BURDEN_DIR = Path(r"D:\_datefac\output\remaining_burden_planning_323p")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\alias_patch_cycle_closure_325p")

FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
SEMANTIC_ALIAS_ASSET_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")


EXPECTED_325O_VALUES = {
    "qa_fail_count": 0,
    "official_rule_visibility_total": 6,
    "official_alias_rules_visible": 6,
    "missing_official_alias_rule_count": 0,
    "wrong_target_metric_count": 0,
    "affected_candidate_count": 45,
    "trusted_gain_325o": 45,
    "review_reduction_325o": 45,
    "out_of_scope_or_rejected_gain_325o": 0,
    "target_conflict_count": 0,
    "adjusted_metric_mismatch_count": 0,
    "diluted_eps_mismatch_count": 0,
    "core_false_mapping_count": 0,
}


EXPECTED_CYCLE_325_VALUES = {
    "official_alias_rule_count_325": 6,
    "trusted_gain_325": 45,
    "review_reduction_325": 45,
    "out_of_scope_or_rejected_gain_325": 0,
    "affected_candidate_count_325": 45,
}


EXPECTED_CUMULATIVE_VALUES = {
    "previous_combined_official_rule_count": 17,
    "previous_combined_trusted_gain": 93,
    "previous_combined_review_reduction": 458,
    "cumulative_official_rule_count_after_325": 23,
    "cumulative_trusted_gain_after_325": 138,
    "cumulative_review_reduction_after_325": 503,
}


STAGE_SUMMARY_FILES = [
    ("325A", Path(r"D:\_datefac\output\alias_candidate_refinement_325a\alias_candidate_refinement_325a_summary.json")),
    ("325B", Path(r"D:\_datefac\output\alias_review_batch_325b\alias_review_batch_325b_summary.json")),
    ("325C", Path(r"D:\_datefac\output\alias_review_batch_sanity_gate_325c\alias_review_batch_sanity_gate_325c_summary.json")),
    ("325D prepare", Path(r"D:\_datefac\output\alias_human_spot_check_325d\alias_human_spot_check_325d_summary.json")),
    ("325D reviewed", Path(r"D:\_datefac\output\alias_human_spot_check_325d_reviewed\alias_human_spot_check_325d_reviewed_summary.json")),
    ("325E", Path(r"D:\_datefac\output\alias_safe_adjudicator_request_325e\alias_safe_adjudicator_request_325e_summary.json")),
    ("325F", Path(r"D:\_datefac\output\alias_adjudicator_response_collection_325f\alias_adjudicator_response_collection_325f_summary.json")),
    ("325G", Path(r"D:\_datefac\output\alias_response_schema_validation_325g\alias_response_schema_validation_325g_summary.json")),
    ("325H prepare", Path(r"D:\_datefac\output\alias_human_confirmation_325h\alias_human_confirmation_325h_summary.json")),
    ("325H reviewed", Path(r"D:\_datefac\output\alias_human_confirmation_325h_reviewed\alias_human_confirmation_325h_reviewed_summary.json")),
    ("325I", Path(r"D:\_datefac\output\alias_human_confirmed_sandbox_replay_325i\alias_human_confirmed_sandbox_replay_325i_summary.json")),
    ("325J", Path(r"D:\_datefac\output\alias_official_rule_candidates_from_325i_325j\alias_official_rule_candidates_from_325i_325j_summary.json")),
    ("325K", Path(r"D:\_datefac\output\controlled_official_proposal_from_325j_325k\controlled_official_proposal_from_325j_325k_summary.json")),
    ("325L", Path(r"D:\_datefac\output\controlled_official_proposal_dry_run_325l\controlled_official_proposal_dry_run_325l_summary.json")),
    ("325M prepare", Path(r"D:\_datefac\output\controlled_alias_proposal_human_approval_325m\controlled_alias_proposal_human_approval_325m_summary.json")),
    ("325M reviewed", Path(r"D:\_datefac\output\controlled_alias_proposal_human_approval_325m_reviewed\controlled_alias_proposal_human_approval_325m_reviewed_summary.json")),
    ("325N", Path(r"D:\_datefac\output\official_alias_patch_application_325n\official_alias_patch_application_325n_summary.json")),
    ("325O", Path(r"D:\_datefac\output\post_patch_regression_validation_325o\post_patch_regression_validation_325o_summary.json")),
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


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _norm(value).lower() in {"1", "true", "yes", "y"}


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
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_alias_patch_cycle_closure_325p_inputs(
    post_patch_regression_dir: Path,
    official_patch_application_dir: Path,
    previous_cycle_closure_dir: Path,
    remaining_burden_dir: Path,
) -> Dict[str, Any]:
    return {
        "summary_325o": _read_json(post_patch_regression_dir / "post_patch_regression_validation_325o_summary.json"),
        "qa_325o": _read_json(post_patch_regression_dir / "post_patch_regression_validation_325o_qa.json"),
        "no_apply_325o": _read_json(post_patch_regression_dir / "post_patch_regression_validation_325o_no_apply_proof.json"),
        "summary_325n": _read_json(official_patch_application_dir / "official_alias_patch_application_325n_summary.json"),
        "summary_324n": _read_json(previous_cycle_closure_dir / "official_scope_patch_cycle_closure_324n_summary.json"),
        "summary_323o": _read_json(Path(r"D:\_datefac\output\official_semantic_patch_cycle_closure_323o\official_semantic_patch_cycle_closure_323o_summary.json")),
        "summary_323p": _read_json(remaining_burden_dir / "remaining_burden_planning_323p_summary.json"),
        "stage_summaries": {stage: _read_json(path) for stage, path in STAGE_SUMMARY_FILES},
    }


def build_alias_patch_cycle_closure_325p(
    summary_325o: Dict[str, Any],
    qa_325o: Dict[str, Any],
    no_apply_325o: Dict[str, Any],
    summary_325n: Dict[str, Any],
    summary_324n: Dict[str, Any],
    summary_323o: Dict[str, Any],
    summary_323p: Dict[str, Any],
    stage_summaries: Dict[str, Dict[str, Any]],
    output_dir: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(SEMANTIC_ALIAS_ASSET_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    add_qa(
        "readiness::325o_decision",
        "PASS" if _norm(summary_325o.get("decision")) == EXPECTED_325O_DECISION else "FAIL",
        _norm(summary_325o.get("decision")),
    )
    for key, expected in EXPECTED_325O_VALUES.items():
        add_qa(
            f"readiness::325o_{key}",
            "PASS" if _safe_int(summary_325o.get(key)) == expected else "FAIL",
            f"expected={expected} actual={summary_325o.get(key, '')}",
        )
    for key in ["rollback_artifact_check_passed", "no_official_asset_modification_during_325o"]:
        add_qa(
            f"readiness::325o_{key}",
            "PASS" if _safe_bool(summary_325o.get(key)) else "FAIL",
            str(summary_325o.get(key, "")),
        )
    add_qa(
        "readiness::325o_qa_json_fail_count",
        "PASS" if _safe_int(qa_325o.get("qa_fail_count")) == 0 else "FAIL",
        str(qa_325o.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::325o_no_apply_written_assets",
        "PASS" if no_apply_325o.get("official_assets_written", []) == [] else "FAIL",
        str(no_apply_325o.get("official_assets_written", "")),
    )

    funnel_counts = {
        "input_alias_inventory_count_325a": _safe_int(stage_summaries.get("325A", {}).get("input_alias_inventory_count")),
        "safe_alias_review_batch_count_325a": _safe_int(stage_summaries.get("325A", {}).get("safe_alias_review_batch_count")),
        "send_to_adjudicator_count_325d": _safe_int(stage_summaries.get("325D reviewed", {}).get("send_to_adjudicator_count")),
        "request_count_325e": _safe_int(stage_summaries.get("325E", {}).get("request_count")),
        "accepted_for_human_confirmation_count_325g": _safe_int(stage_summaries.get("325G", {}).get("accepted_for_human_confirmation_count")),
        "confirmed_count_325h": _safe_int(stage_summaries.get("325H reviewed", {}).get("confirmed_count")),
        "sandbox_alias_rule_count_325i": _safe_int(stage_summaries.get("325I", {}).get("sandbox_alias_rule_count")),
        "ready_candidate_count_325j": _safe_int(stage_summaries.get("325J", {}).get("ready_for_controlled_proposal_count")),
        "ready_proposal_count_325k": _safe_int(stage_summaries.get("325K", {}).get("ready_for_dry_run_proposal_count")),
        "patch_operation_count_325l": _safe_int(stage_summaries.get("325L", {}).get("patch_operation_count")),
        "approved_patch_operation_count_325m": _safe_int(stage_summaries.get("325M reviewed", {}).get("approved_patch_operation_count")),
        "applied_or_idempotent_operation_count_325n": _safe_int(summary_325n.get("applied_or_idempotent_operation_count")),
        "visible_official_alias_rule_count_325o": _safe_int(summary_325o.get("official_alias_rules_visible")),
    }

    for key, expected in [
        ("safe_alias_review_batch_count_325a", 12),
        ("send_to_adjudicator_count_325d", 6),
        ("request_count_325e", 6),
        ("accepted_for_human_confirmation_count_325g", 6),
        ("confirmed_count_325h", 6),
        ("sandbox_alias_rule_count_325i", 6),
        ("ready_candidate_count_325j", 6),
        ("ready_proposal_count_325k", 6),
        ("patch_operation_count_325l", 6),
        ("approved_patch_operation_count_325m", 6),
        ("applied_or_idempotent_operation_count_325n", 6),
        ("visible_official_alias_rule_count_325o", 6),
    ]:
        add_qa(
            f"funnel::{key}",
            "PASS" if funnel_counts[key] == expected else "FAIL",
            f"expected={expected} actual={funnel_counts[key]}",
        )

    official_alias_rule_count_325 = _safe_int(summary_325o.get("official_alias_rules_visible"))
    trusted_gain_325 = _safe_int(summary_325o.get("trusted_gain_325o"))
    review_reduction_325 = _safe_int(summary_325o.get("review_reduction_325o"))
    out_of_scope_or_rejected_gain_325 = _safe_int(summary_325o.get("out_of_scope_or_rejected_gain_325o"))
    affected_candidate_count_325 = _safe_int(summary_325o.get("affected_candidate_count"))
    cycle_325_values = {
        "official_alias_rule_count_325": official_alias_rule_count_325,
        "trusted_gain_325": trusted_gain_325,
        "review_reduction_325": review_reduction_325,
        "out_of_scope_or_rejected_gain_325": out_of_scope_or_rejected_gain_325,
        "affected_candidate_count_325": affected_candidate_count_325,
    }
    for key, expected in EXPECTED_CYCLE_325_VALUES.items():
        add_qa(
            f"cycle_325::{key}",
            "PASS" if cycle_325_values[key] == expected else "FAIL",
            f"expected={expected} actual={cycle_325_values[key]}",
        )

    duplicate_delta_count = _safe_int(summary_325o.get("duplicate_delta_count"))
    target_conflict_count = _safe_int(summary_325o.get("target_conflict_count"))
    adjusted_metric_mismatch_count = _safe_int(summary_325o.get("adjusted_metric_mismatch_count"))
    diluted_eps_mismatch_count = _safe_int(summary_325o.get("diluted_eps_mismatch_count"))
    core_false_mapping_count = _safe_int(summary_325o.get("core_false_mapping_count"))
    rollback_artifact_check_passed = _safe_bool(summary_325o.get("rollback_artifact_check_passed"))
    for key, actual, expected in [
        ("duplicate_delta_count", duplicate_delta_count, 0),
        ("target_conflict_count", target_conflict_count, 0),
        ("adjusted_metric_mismatch_count", adjusted_metric_mismatch_count, 0),
        ("diluted_eps_mismatch_count", diluted_eps_mismatch_count, 0),
        ("core_false_mapping_count", core_false_mapping_count, 0),
    ]:
        add_qa(f"safety::{key}", "PASS" if actual == expected else "FAIL", f"expected={expected} actual={actual}")
    add_qa(
        "safety::rollback_artifact_check_passed",
        "PASS" if rollback_artifact_check_passed else "FAIL",
        str(summary_325o.get("rollback_artifact_check_passed", "")),
    )

    previous_combined_official_rule_count = _safe_int(summary_324n.get("combined_official_rule_count"))
    previous_combined_trusted_gain = _safe_int(summary_324n.get("combined_trusted_gain"))
    previous_combined_review_reduction = _safe_int(summary_324n.get("combined_review_reduction"))
    previous_combined_out_of_scope_or_rejected_gain = _safe_int(summary_324n.get("combined_out_of_scope_or_rejected_gain"))
    cumulative_official_rule_count_after_325 = previous_combined_official_rule_count + official_alias_rule_count_325
    cumulative_trusted_gain_after_325 = previous_combined_trusted_gain + trusted_gain_325
    cumulative_review_reduction_after_325 = previous_combined_review_reduction + review_reduction_325
    cumulative_out_of_scope_or_rejected_gain_after_325 = previous_combined_out_of_scope_or_rejected_gain + out_of_scope_or_rejected_gain_325
    cumulative_values = {
        "previous_combined_official_rule_count": previous_combined_official_rule_count,
        "previous_combined_trusted_gain": previous_combined_trusted_gain,
        "previous_combined_review_reduction": previous_combined_review_reduction,
        "cumulative_official_rule_count_after_325": cumulative_official_rule_count_after_325,
        "cumulative_trusted_gain_after_325": cumulative_trusted_gain_after_325,
        "cumulative_review_reduction_after_325": cumulative_review_reduction_after_325,
    }
    for key, expected in EXPECTED_CUMULATIVE_VALUES.items():
        add_qa(
            f"cumulative::{key}",
            "PASS" if cumulative_values[key] == expected else "FAIL",
            f"expected={expected} actual={cumulative_values[key]}",
        )

    remaining_burden_loaded = bool(summary_323p)
    remaining_unknown_metric_candidate_count = _safe_int(summary_323p.get("remaining_unknown_metric_candidate_count"))
    remaining_unit_unknown_candidate_count = _safe_int(summary_323p.get("remaining_unit_unknown_candidate_count"))
    remaining_manual_review_count = _safe_int(summary_323p.get("remaining_manual_review_count"))
    add_qa(
        "remaining_burden::323p_loaded",
        "PASS" if remaining_burden_loaded else "WARN",
        "inherited from 323P / pre-325" if remaining_burden_loaded else "323P summary missing",
    )

    residual_risks = [
        "existing alias asset contains historical mojibake or encoding artifacts",
        "325O validates official visibility, target mapping, and cached impact rather than full production semantic recalculation",
        "remaining burden not recomputed unless a reliable current artifact exists",
    ]
    residual_warning_count = len(residual_risks)

    primary_next_direction = "330A Trust Engine Consolidation"
    secondary_next_direction = "end-to-end unfamiliar PDF benchmark and delivery quality report"

    alias_hash_after = _sha256_file(SEMANTIC_ALIAS_ASSET_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    no_official_asset_modification_during_325p = (
        alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after
    )
    add_qa(
        "safety::no_official_asset_modification_during_325p",
        "PASS" if no_official_asset_modification_during_325p else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )

    stage_rows: List[Dict[str, Any]] = []
    for stage, stage_summary in stage_summaries.items():
        stage_rows.append(
            {
                "stage": stage,
                "summary_loaded": bool(stage_summary),
                "decision": _norm(stage_summary.get("decision")),
                "qa_fail_count": _safe_int(stage_summary.get("qa_fail_count")),
                "output_dir": _norm(stage_summary.get("output_dir")),
            }
        )

    funnel_df = pd.DataFrame(
        [
            {"metric": "325A input_alias_inventory_count", "value": funnel_counts["input_alias_inventory_count_325a"]},
            {"metric": "325A safe_alias_review_batch_count", "value": funnel_counts["safe_alias_review_batch_count_325a"]},
            {"metric": "325D send_to_adjudicator_count", "value": funnel_counts["send_to_adjudicator_count_325d"]},
            {"metric": "325E request_count", "value": funnel_counts["request_count_325e"]},
            {"metric": "325G accepted_for_human_confirmation_count", "value": funnel_counts["accepted_for_human_confirmation_count_325g"]},
            {"metric": "325H confirmed_count", "value": funnel_counts["confirmed_count_325h"]},
            {"metric": "325I sandbox_alias_rule_count", "value": funnel_counts["sandbox_alias_rule_count_325i"]},
            {"metric": "325J ready_candidate_count", "value": funnel_counts["ready_candidate_count_325j"]},
            {"metric": "325K ready_proposal_count", "value": funnel_counts["ready_proposal_count_325k"]},
            {"metric": "325L patch_operation_count", "value": funnel_counts["patch_operation_count_325l"]},
            {"metric": "325M approved_patch_operation_count", "value": funnel_counts["approved_patch_operation_count_325m"]},
            {"metric": "325N applied_or_idempotent_operation_count", "value": funnel_counts["applied_or_idempotent_operation_count_325n"]},
            {"metric": "325O visible_official_alias_rule_count", "value": funnel_counts["visible_official_alias_rule_count_325o"]},
        ]
    ).fillna("")

    cycle_summary_df = pd.DataFrame(
        [
            {
                "cycle": "325",
                "official_alias_rule_count": official_alias_rule_count_325,
                "trusted_gain": trusted_gain_325,
                "review_reduction": review_reduction_325,
                "out_of_scope_or_rejected_gain": out_of_scope_or_rejected_gain_325,
                "affected_candidate_count": affected_candidate_count_325,
                "duplicate_delta_count": duplicate_delta_count,
                "target_conflict_count": target_conflict_count,
                "adjusted_metric_mismatch_count": adjusted_metric_mismatch_count,
                "diluted_eps_mismatch_count": diluted_eps_mismatch_count,
                "core_false_mapping_count": core_false_mapping_count,
            },
            {
                "cycle": "combined_through_324",
                "official_alias_rule_count": previous_combined_official_rule_count,
                "trusted_gain": previous_combined_trusted_gain,
                "review_reduction": previous_combined_review_reduction,
                "out_of_scope_or_rejected_gain": previous_combined_out_of_scope_or_rejected_gain,
                "affected_candidate_count": "",
                "duplicate_delta_count": "",
                "target_conflict_count": "",
                "adjusted_metric_mismatch_count": "",
                "diluted_eps_mismatch_count": "",
                "core_false_mapping_count": "",
            },
            {
                "cycle": "combined_through_325",
                "official_alias_rule_count": cumulative_official_rule_count_after_325,
                "trusted_gain": cumulative_trusted_gain_after_325,
                "review_reduction": cumulative_review_reduction_after_325,
                "out_of_scope_or_rejected_gain": cumulative_out_of_scope_or_rejected_gain_after_325,
                "affected_candidate_count": "",
                "duplicate_delta_count": "",
                "target_conflict_count": "",
                "adjusted_metric_mismatch_count": "",
                "diluted_eps_mismatch_count": "",
                "core_false_mapping_count": "",
            },
        ]
    ).fillna("")

    remaining_burden_df = pd.DataFrame(
        [
            {
                "metric": "remaining_unknown_metric_candidate_count",
                "value": remaining_unknown_metric_candidate_count,
                "source": "323P",
                "status": "inherited_pre_325_not_recomputed",
            },
            {
                "metric": "remaining_unit_unknown_candidate_count",
                "value": remaining_unit_unknown_candidate_count,
                "source": "323P",
                "status": "inherited_pre_325_not_recomputed",
            },
            {
                "metric": "remaining_manual_review_count",
                "value": remaining_manual_review_count,
                "source": "323P",
                "status": "inherited_pre_325_not_recomputed",
            },
        ]
    ).fillna("")

    residual_risks_df = pd.DataFrame(
        [{"risk": risk, "severity": "warning"} for risk in residual_risks]
    ).fillna("")

    recommendations_df = pd.DataFrame(
        [
            {
                "rank": "primary",
                "recommended_next_direction": primary_next_direction,
                "reason": "325 alias cycle is closed and official alias gains are now accumulated; the next leverage point is trust consolidation rather than another patch loop.",
            },
            {
                "rank": "secondary",
                "recommended_next_direction": secondary_next_direction,
                "reason": "Residual delivery quality risk remains on unfamiliar PDFs even when semantic patching succeeds.",
            },
        ]
    ).fillna("")

    official_asset_proof_df = pd.DataFrame(
        [
            {
                "asset_path": str(SEMANTIC_ALIAS_ASSET_PATH),
                "hash_before_325p": alias_hash_before,
                "hash_after_325p": alias_hash_after,
                "modified_during_325p": alias_hash_before != alias_hash_after,
            },
            {
                "asset_path": str(FORMAL_SCOPE_RULES_PATH),
                "hash_before_325p": scope_hash_before,
                "hash_after_325p": scope_hash_after,
                "modified_during_325p": scope_hash_before != scope_hash_after,
            },
        ]
    ).fillna("")

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    decision = (
        READY_WITH_WARNINGS_DECISION
        if qa_fail_count == 0 and residual_warning_count > 0
        else READY_DECISION if qa_fail_count == 0
        else NOT_READY_DECISION
    )

    summary = {
        "stage": "325P",
        "output_dir": str(output_dir),
        "input_alias_inventory_count_325a": funnel_counts["input_alias_inventory_count_325a"],
        "safe_alias_review_batch_count_325a": funnel_counts["safe_alias_review_batch_count_325a"],
        "send_to_adjudicator_count_325d": funnel_counts["send_to_adjudicator_count_325d"],
        "request_count_325e": funnel_counts["request_count_325e"],
        "accepted_for_human_confirmation_count_325g": funnel_counts["accepted_for_human_confirmation_count_325g"],
        "confirmed_count_325h": funnel_counts["confirmed_count_325h"],
        "sandbox_alias_rule_count_325i": funnel_counts["sandbox_alias_rule_count_325i"],
        "ready_candidate_count_325j": funnel_counts["ready_candidate_count_325j"],
        "ready_proposal_count_325k": funnel_counts["ready_proposal_count_325k"],
        "patch_operation_count_325l": funnel_counts["patch_operation_count_325l"],
        "approved_patch_operation_count_325m": funnel_counts["approved_patch_operation_count_325m"],
        "applied_or_idempotent_operation_count_325n": funnel_counts["applied_or_idempotent_operation_count_325n"],
        "visible_official_alias_rule_count_325o": funnel_counts["visible_official_alias_rule_count_325o"],
        "official_alias_rule_count_325": official_alias_rule_count_325,
        "trusted_gain_325": trusted_gain_325,
        "review_reduction_325": review_reduction_325,
        "out_of_scope_or_rejected_gain_325": out_of_scope_or_rejected_gain_325,
        "affected_candidate_count_325": affected_candidate_count_325,
        "duplicate_delta_count": duplicate_delta_count,
        "target_conflict_count": target_conflict_count,
        "adjusted_metric_mismatch_count": adjusted_metric_mismatch_count,
        "diluted_eps_mismatch_count": diluted_eps_mismatch_count,
        "core_false_mapping_count": core_false_mapping_count,
        "rollback_artifact_check_passed": rollback_artifact_check_passed,
        "previous_combined_official_rule_count": previous_combined_official_rule_count,
        "previous_combined_trusted_gain": previous_combined_trusted_gain,
        "previous_combined_review_reduction": previous_combined_review_reduction,
        "previous_combined_out_of_scope_or_rejected_gain": previous_combined_out_of_scope_or_rejected_gain,
        "cumulative_official_rule_count_after_325": cumulative_official_rule_count_after_325,
        "cumulative_trusted_gain_after_325": cumulative_trusted_gain_after_325,
        "cumulative_review_reduction_after_325": cumulative_review_reduction_after_325,
        "cumulative_out_of_scope_or_rejected_gain_after_325": cumulative_out_of_scope_or_rejected_gain_after_325,
        "remaining_unknown_metric_candidate_count": remaining_unknown_metric_candidate_count,
        "remaining_unit_unknown_candidate_count": remaining_unit_unknown_candidate_count,
        "remaining_manual_review_count": remaining_manual_review_count,
        "remaining_burden_status": "inherited_from_323p_pre_325_not_recomputed" if remaining_burden_loaded else "missing_323p",
        "residual_risk_count": residual_warning_count,
        "primary_next_direction": primary_next_direction,
        "secondary_next_direction": secondary_next_direction,
        "no_official_asset_modification_during_325p": no_official_asset_modification_during_325p,
        "official_assets_written": [],
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": decision,
    }

    closure_json = {
        "funnel_counts_325": funnel_counts,
        "cycle_325": cycle_325_values,
        "previous_combined": {
            "official_rule_count": previous_combined_official_rule_count,
            "trusted_gain": previous_combined_trusted_gain,
            "review_reduction": previous_combined_review_reduction,
            "out_of_scope_or_rejected_gain": previous_combined_out_of_scope_or_rejected_gain,
        },
        "combined_through_325": {
            "official_rule_count": cumulative_official_rule_count_after_325,
            "trusted_gain": cumulative_trusted_gain_after_325,
            "review_reduction": cumulative_review_reduction_after_325,
            "out_of_scope_or_rejected_gain": cumulative_out_of_scope_or_rejected_gain_after_325,
        },
        "residual_risks": residual_risks,
        "remaining_burden": remaining_burden_df.to_dict(orient="records"),
        "next_cycle_recommendations": recommendations_df.to_dict(orient="records"),
    }

    no_apply_proof_json = {
        "stage": "325P",
        "decision": decision,
        "files_read": [
            str(DEFAULT_POST_PATCH_REGRESSION_DIR / "post_patch_regression_validation_325o_summary.json"),
            str(DEFAULT_OFFICIAL_PATCH_APPLICATION_DIR / "official_alias_patch_application_325n_summary.json"),
            str(DEFAULT_PREVIOUS_CYCLE_CLOSURE_DIR / "official_scope_patch_cycle_closure_324n_summary.json"),
            str(Path(r"D:\_datefac\output\official_semantic_patch_cycle_closure_323o\official_semantic_patch_cycle_closure_323o_summary.json")),
            str(DEFAULT_REMAINING_BURDEN_DIR / "remaining_burden_planning_323p_summary.json"),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
        "official_assets_before_325p": {
            str(SEMANTIC_ALIAS_ASSET_PATH): alias_hash_before,
            str(FORMAL_SCOPE_RULES_PATH): scope_hash_before,
        },
        "official_assets_after_325p": {
            str(SEMANTIC_ALIAS_ASSET_PATH): alias_hash_after,
            str(FORMAL_SCOPE_RULES_PATH): scope_hash_after,
        },
        "official_assets_written": [],
        "no_official_asset_modification_during_325p": no_official_asset_modification_during_325p,
    }

    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
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

    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "cached_outputs_only",
                "detail": "325P summarizes cached 322 through 325 outputs and does not rerun extraction, adjudication, sandbox replay, or semantic application.",
            },
            {
                "limitation": "historical_alias_asset_mojibake",
                "detail": "Official alias asset still contains historical mojibake or encoding artifacts.",
            },
            {
                "limitation": "remaining_burden_not_recomputed",
                "detail": "Remaining burden metrics are inherited from 323P unless a newer reliable planning artifact exists.",
            },
        ]
    ).fillna("")

    return {
        "summary": summary,
        "qa_json": qa_json,
        "closure_json": closure_json,
        "no_apply_proof_json": no_apply_proof_json,
        "funnel_df": funnel_df,
        "cycle_summary_df": cycle_summary_df,
        "stage_timeline_df": pd.DataFrame(stage_rows).fillna(""),
        "remaining_burden_df": remaining_burden_df,
        "residual_risks_df": residual_risks_df,
        "recommendations_df": recommendations_df,
        "official_asset_proof_df": official_asset_proof_df,
        "qa_summary_df": qa_summary_df,
        "qa_checks_df": qa_df,
        "known_limitations_df": known_limitations_df,
    }
