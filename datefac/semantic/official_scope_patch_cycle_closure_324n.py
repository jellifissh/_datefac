from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


EXPECTED_324M_DECISION = "POST_PATCH_REGRESSION_VALIDATION_324M_READY_WITH_WARNINGS"
READY_DECISION = "OFFICIAL_SCOPE_PATCH_CYCLE_324N_CLOSED_READY_FOR_NEXT_CYCLE_PLANNING"
NOT_READY_DECISION = "OFFICIAL_SCOPE_PATCH_CYCLE_324N_NOT_READY"

DEFAULT_POST_PATCH_REGRESSION_DIR = Path(r"D:\_datefac\output\post_patch_regression_validation_324m")
DEFAULT_OFFICIAL_PATCH_APPLICATION_DIR = Path(r"D:\_datefac\output\official_patch_application_324l")
DEFAULT_PREVIOUS_CYCLE_CLOSURE_DIR = Path(r"D:\_datefac\output\official_semantic_patch_cycle_closure_323o")
DEFAULT_REMAINING_BURDEN_DIR = Path(r"D:\_datefac\output\remaining_burden_planning_323p")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\official_scope_patch_cycle_closure_324n")

FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
SEMANTIC_ALIAS_ASSET_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")


EXPECTED_324M_VALUES = {
    "qa_fail_count": 0,
    "official_rule_visibility_total": 1,
    "scope_rules_visible": 1,
    "alias_rules_visible": 0,
    "affected_candidate_count": 42,
    "trusted_gain_324m": 0,
    "review_reduction_324m": 42,
    "out_of_scope_or_rejected_gain_324m": 42,
    "core_false_exclusion_count": 0,
    "new_duplicate_delta_count": 0,
    "conflict_count": 0,
}


EXPECTED_CYCLE_324_VALUES = {
    "official_rule_count_324": 1,
    "scope_rule_count_324": 1,
    "alias_rule_count_324": 0,
    "trusted_gain_324": 0,
    "review_reduction_324": 42,
    "out_of_scope_or_rejected_gain_324": 42,
    "affected_candidate_count_324": 42,
    "core_false_exclusion_count_324": 0,
    "new_duplicate_delta_count_324": 0,
    "conflict_count_324": 0,
}


STAGE_SUMMARY_FILES = [
    ("324A", Path(r"D:\_datefac\output\scope_noise_refinement_324a\scope_noise_refinement_324a_summary.json")),
    ("324B prepare", Path(r"D:\_datefac\output\scope_noise_human_review_324b\scope_noise_human_review_324b_summary.json")),
    ("324B reviewed", Path(r"D:\_datefac\output\scope_noise_human_review_324b_reviewed\scope_noise_human_review_324b_summary.json")),
    ("324C", Path(r"D:\_datefac\output\scope_noise_safe_adjudicator_request_324c\scope_noise_safe_adjudicator_request_324c_summary.json")),
    ("324D", Path(r"D:\_datefac\output\scope_noise_adjudicator_response_collection_324d\scope_noise_adjudicator_response_collection_324d_summary.json")),
    ("324E", Path(r"D:\_datefac\output\scope_noise_response_schema_validation_324e\scope_noise_response_schema_validation_324e_summary.json")),
    ("324F prepare", Path(r"D:\_datefac\output\scope_noise_human_confirmation_324f\scope_noise_human_confirmation_324f_summary.json")),
    ("324F reviewed", Path(r"D:\_datefac\output\scope_noise_human_confirmation_324f_reviewed\scope_noise_human_confirmation_324f_summary.json")),
    ("324G", Path(r"D:\_datefac\output\scope_noise_human_confirmed_sandbox_replay_324g\scope_noise_human_confirmed_sandbox_replay_324g_summary.json")),
    ("324H", Path(r"D:\_datefac\output\official_rule_candidate_from_324g_324h\official_rule_candidate_from_324g_324h_summary.json")),
    ("324I", Path(r"D:\_datefac\output\controlled_official_proposal_from_324h_324i\controlled_official_proposal_from_324h_324i_summary.json")),
    ("324J", Path(r"D:\_datefac\output\controlled_official_proposal_dry_run_324j\controlled_official_proposal_dry_run_324j_summary.json")),
    ("324K prepare", Path(r"D:\_datefac\output\controlled_official_proposal_human_approval_324k\controlled_official_proposal_human_approval_324k_summary.json")),
    ("324K reviewed", Path(r"D:\_datefac\output\controlled_official_proposal_human_approval_324k_reviewed\controlled_official_proposal_human_approval_324k_summary.json")),
    ("324L", Path(r"D:\_datefac\output\official_patch_application_324l\official_patch_application_324l_summary.json")),
    ("324M", Path(r"D:\_datefac\output\post_patch_regression_validation_324m\post_patch_regression_validation_324m_summary.json")),
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


def load_official_scope_patch_cycle_closure_324n_inputs(
    post_patch_regression_dir: Path,
    official_patch_application_dir: Path,
    previous_cycle_closure_dir: Path,
    remaining_burden_dir: Path,
) -> Dict[str, Any]:
    return {
        "summary_324m": _read_json(post_patch_regression_dir / "post_patch_regression_validation_324m_summary.json"),
        "qa_324m": _read_json(post_patch_regression_dir / "post_patch_regression_validation_324m_qa.json"),
        "no_apply_324m": _read_json(post_patch_regression_dir / "post_patch_regression_validation_324m_no_apply_proof.json"),
        "summary_324l": _read_json(official_patch_application_dir / "official_patch_application_324l_summary.json"),
        "summary_323o": _read_json(previous_cycle_closure_dir / "official_semantic_patch_cycle_closure_323o_summary.json"),
        "summary_323p": _read_json(remaining_burden_dir / "remaining_burden_planning_323p_summary.json"),
        "stage_summaries": {stage: _read_json(path) for stage, path in STAGE_SUMMARY_FILES},
    }


def build_official_scope_patch_cycle_closure_324n(
    summary_324m: Dict[str, Any],
    qa_324m: Dict[str, Any],
    no_apply_324m: Dict[str, Any],
    summary_324l: Dict[str, Any],
    summary_323o: Dict[str, Any],
    summary_323p: Dict[str, Any],
    stage_summaries: Dict[str, Dict[str, Any]],
    output_dir: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    alias_hash_before = _sha256_file(SEMANTIC_ALIAS_ASSET_PATH)

    add_qa(
        "readiness::324m_decision",
        "PASS" if _norm(summary_324m.get("decision")) == EXPECTED_324M_DECISION else "FAIL",
        _norm(summary_324m.get("decision")),
    )
    for key, expected in EXPECTED_324M_VALUES.items():
        add_qa(
            f"readiness::324m_{key}",
            "PASS" if _safe_int(summary_324m.get(key)) == expected else "FAIL",
            f"expected={expected} actual={summary_324m.get(key, '')}",
        )
    for key in ["rollback_artifact_check_passed", "no_official_asset_modification_during_324m"]:
        add_qa(
            f"readiness::324m_{key}",
            "PASS" if _safe_bool(summary_324m.get(key)) else "FAIL",
            str(summary_324m.get(key, "")),
        )
    add_qa(
        "readiness::324m_qa_json_fail_count",
        "PASS" if _safe_int(qa_324m.get("qa_fail_count")) == 0 else "FAIL",
        str(qa_324m.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::324m_no_apply_written_assets",
        "PASS" if no_apply_324m.get("official_assets_written", []) == [] else "FAIL",
        str(no_apply_324m.get("official_assets_written", "")),
    )

    official_rule_count_324 = _safe_int(summary_324m.get("official_rule_visibility_total"))
    scope_rule_count_324 = _safe_int(summary_324m.get("scope_rules_visible"))
    alias_rule_count_324 = _safe_int(summary_324m.get("alias_rules_visible"))
    trusted_gain_324 = _safe_int(summary_324m.get("trusted_gain_324m"))
    review_reduction_324 = _safe_int(summary_324m.get("review_reduction_324m"))
    out_of_scope_or_rejected_gain_324 = _safe_int(summary_324m.get("out_of_scope_or_rejected_gain_324m"))
    affected_candidate_count_324 = _safe_int(summary_324m.get("affected_candidate_count"))
    core_false_exclusion_count_324 = _safe_int(summary_324m.get("core_false_exclusion_count"))
    current_duplicate_count = _safe_int(summary_324m.get("current_duplicate_count"))
    new_duplicate_delta_count_324 = _safe_int(summary_324m.get("new_duplicate_delta_count"))
    conflict_count_324 = _safe_int(summary_324m.get("conflict_count"))

    cycle_324_values = {
        "official_rule_count_324": official_rule_count_324,
        "scope_rule_count_324": scope_rule_count_324,
        "alias_rule_count_324": alias_rule_count_324,
        "trusted_gain_324": trusted_gain_324,
        "review_reduction_324": review_reduction_324,
        "out_of_scope_or_rejected_gain_324": out_of_scope_or_rejected_gain_324,
        "affected_candidate_count_324": affected_candidate_count_324,
        "core_false_exclusion_count_324": core_false_exclusion_count_324,
        "new_duplicate_delta_count_324": new_duplicate_delta_count_324,
        "conflict_count_324": conflict_count_324,
    }
    for key, expected in EXPECTED_CYCLE_324_VALUES.items():
        add_qa(
            f"cycle_324::{key}",
            "PASS" if cycle_324_values[key] == expected else "FAIL",
            f"expected={expected} actual={cycle_324_values[key]}",
        )

    previous_official_rule_count = _safe_int(summary_323o.get("combined_rules"))
    previous_trusted_gain = _safe_int(summary_323o.get("combined_trusted_gain"))
    previous_review_reduction = _safe_int(summary_323o.get("combined_review_reduction"))
    previous_out_of_scope_or_rejected_gain = _safe_int(summary_323o.get("combined_out_of_scope_or_rejected_gain"))
    combined_official_rule_count = previous_official_rule_count + official_rule_count_324
    combined_trusted_gain = previous_trusted_gain + trusted_gain_324
    combined_review_reduction = previous_review_reduction + review_reduction_324
    combined_out_of_scope_or_rejected_gain = (
        previous_out_of_scope_or_rejected_gain + out_of_scope_or_rejected_gain_324
    )
    for name, actual, expected in [
        ("previous_official_rule_count", previous_official_rule_count, 16),
        ("previous_trusted_gain", previous_trusted_gain, 93),
        ("previous_review_reduction", previous_review_reduction, 416),
        ("combined_official_rule_count", combined_official_rule_count, 17),
        ("combined_trusted_gain", combined_trusted_gain, 93),
        ("combined_review_reduction", combined_review_reduction, 458),
    ]:
        add_qa(f"cumulative::{name}", "PASS" if actual == expected else "FAIL", f"expected={expected} actual={actual}")

    remaining_burden_loaded = bool(summary_323p)
    remaining_unknown_metric_candidate_count = _safe_int(summary_323p.get("remaining_unknown_metric_candidate_count"))
    remaining_unit_unknown_candidate_count = _safe_int(summary_323p.get("remaining_unit_unknown_candidate_count"))
    remaining_manual_review_count = _safe_int(summary_323p.get("remaining_manual_review_count"))
    add_qa(
        "remaining_burden::323p_loaded",
        "PASS" if remaining_burden_loaded else "WARN",
        "inherited from 323P / pre-324" if remaining_burden_loaded else "323P summary missing",
    )

    warning_status = "historical duplicates unchanged only"
    add_qa(
        "warnings::historical_duplicates_unchanged_only",
        "PASS" if current_duplicate_count == 3 and new_duplicate_delta_count_324 == 0 else "FAIL",
        f"current_duplicate_count={current_duplicate_count} new_duplicate_delta_count={new_duplicate_delta_count_324}",
    )

    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    alias_hash_after = _sha256_file(SEMANTIC_ALIAS_ASSET_PATH)
    no_official_asset_modification_during_324n = (
        scope_hash_before == scope_hash_after and alias_hash_before == alias_hash_after
    )
    add_qa(
        "safety::no_official_asset_modification_during_324n",
        "PASS" if no_official_asset_modification_during_324n else "FAIL",
        f"scope_before={scope_hash_before} scope_after={scope_hash_after} alias_before={alias_hash_before} alias_after={alias_hash_after}",
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

    cycle_summary_df = pd.DataFrame(
        [
            {
                "cycle": "322+323",
                "official_rule_count": previous_official_rule_count,
                "scope_rule_count": "",
                "alias_rule_count": "",
                "trusted_gain": previous_trusted_gain,
                "review_reduction": previous_review_reduction,
                "out_of_scope_or_rejected_gain": previous_out_of_scope_or_rejected_gain,
                "affected_candidate_count": "",
                "warning_status": _norm(summary_323o.get("warning_323")),
            },
            {
                "cycle": "324",
                "official_rule_count": official_rule_count_324,
                "scope_rule_count": scope_rule_count_324,
                "alias_rule_count": alias_rule_count_324,
                "trusted_gain": trusted_gain_324,
                "review_reduction": review_reduction_324,
                "out_of_scope_or_rejected_gain": out_of_scope_or_rejected_gain_324,
                "affected_candidate_count": affected_candidate_count_324,
                "warning_status": warning_status,
            },
            {
                "cycle": "combined_through_324",
                "official_rule_count": combined_official_rule_count,
                "scope_rule_count": "",
                "alias_rule_count": "",
                "trusted_gain": combined_trusted_gain,
                "review_reduction": combined_review_reduction,
                "out_of_scope_or_rejected_gain": combined_out_of_scope_or_rejected_gain,
                "affected_candidate_count": "",
                "warning_status": warning_status,
            },
        ]
    ).fillna("")

    remaining_burden_df = pd.DataFrame(
        [
            {
                "metric": "remaining_unknown_metric_candidate_count",
                "value": remaining_unknown_metric_candidate_count,
                "source": "323P",
                "status": "inherited_pre_324_not_recomputed",
            },
            {
                "metric": "remaining_unit_unknown_candidate_count",
                "value": remaining_unit_unknown_candidate_count,
                "source": "323P",
                "status": "inherited_pre_324_not_recomputed",
            },
            {
                "metric": "remaining_manual_review_count",
                "value": remaining_manual_review_count,
                "source": "323P",
                "status": "inherited_pre_324_not_recomputed",
            },
        ]
    ).fillna("")

    recommendations = [
        {
            "rank": "primary",
            "recommended_next_cycle_direction": "alias_candidates",
            "reason": "scope_noise refined queue now mostly exhausted after 324A/324L, while alias review-ready inventory remains larger but riskier.",
        },
        {
            "rank": "secondary",
            "recommended_next_cycle_direction": "duplicate_cleanup_or_unit_holdout_diagnosis",
            "reason": "historical duplicates remain unchanged and unit-related holdout remains unsafe for primary automation without better evidence.",
        },
    ]

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = (
        qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist()
        if not qa_df.empty
        else []
    )
    decision = READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION

    summary = {
        "stage": "324N",
        "output_dir": str(output_dir),
        "official_rule_count_324": official_rule_count_324,
        "scope_rule_count_324": scope_rule_count_324,
        "alias_rule_count_324": alias_rule_count_324,
        "trusted_gain_324": trusted_gain_324,
        "review_reduction_324": review_reduction_324,
        "out_of_scope_or_rejected_gain_324": out_of_scope_or_rejected_gain_324,
        "affected_candidate_count_324": affected_candidate_count_324,
        "core_false_exclusion_count_324": core_false_exclusion_count_324,
        "current_duplicate_count": current_duplicate_count,
        "new_duplicate_delta_count_324": new_duplicate_delta_count_324,
        "conflict_count_324": conflict_count_324,
        "rollback_artifact_check_passed_324": _safe_bool(summary_324m.get("rollback_artifact_check_passed")),
        "previous_combined_official_rule_count": previous_official_rule_count,
        "previous_combined_trusted_gain": previous_trusted_gain,
        "previous_combined_review_reduction": previous_review_reduction,
        "previous_combined_out_of_scope_or_rejected_gain": previous_out_of_scope_or_rejected_gain,
        "combined_official_rule_count": combined_official_rule_count,
        "combined_trusted_gain": combined_trusted_gain,
        "combined_review_reduction": combined_review_reduction,
        "combined_out_of_scope_or_rejected_gain": combined_out_of_scope_or_rejected_gain,
        "remaining_unknown_metric_candidate_count": remaining_unknown_metric_candidate_count,
        "remaining_unit_unknown_candidate_count": remaining_unit_unknown_candidate_count,
        "remaining_manual_review_count": remaining_manual_review_count,
        "remaining_burden_status": "inherited_from_323p_pre_324_not_recomputed" if remaining_burden_loaded else "missing_323p",
        "warning_status": warning_status,
        "recommended_next_cycle_direction_primary": "alias_candidates",
        "recommended_next_cycle_direction_secondary": "duplicate_cleanup_or_unit_holdout_diagnosis",
        "recommendation_reason": recommendations[0]["reason"],
        "no_official_asset_modification_during_324n": no_official_asset_modification_during_324n,
        "official_assets_written": [],
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": decision,
    }

    closure_json = {
        "cycle_324": cycle_324_values,
        "previous_combined": {
            "official_rule_count": previous_official_rule_count,
            "trusted_gain": previous_trusted_gain,
            "review_reduction": previous_review_reduction,
            "out_of_scope_or_rejected_gain": previous_out_of_scope_or_rejected_gain,
        },
        "combined_through_324": {
            "official_rule_count": combined_official_rule_count,
            "trusted_gain": combined_trusted_gain,
            "review_reduction": combined_review_reduction,
            "out_of_scope_or_rejected_gain": combined_out_of_scope_or_rejected_gain,
        },
        "warning_status": {
            "status": warning_status,
            "current_duplicate_count": current_duplicate_count,
            "new_duplicate_delta_count": new_duplicate_delta_count_324,
        },
        "remaining_burden": remaining_burden_df.to_dict(orient="records"),
        "next_cycle_recommendations": recommendations,
    }
    no_apply_proof_json = {
        "stage": "324N",
        "decision": decision,
        "files_read": [
            str(DEFAULT_POST_PATCH_REGRESSION_DIR / "post_patch_regression_validation_324m_summary.json"),
            str(DEFAULT_OFFICIAL_PATCH_APPLICATION_DIR / "official_patch_application_324l_summary.json"),
            str(DEFAULT_PREVIOUS_CYCLE_CLOSURE_DIR / "official_semantic_patch_cycle_closure_323o_summary.json"),
            str(DEFAULT_REMAINING_BURDEN_DIR / "remaining_burden_planning_323p_summary.json"),
            str(FORMAL_SCOPE_RULES_PATH),
            str(SEMANTIC_ALIAS_ASSET_PATH),
        ],
        "official_assets_before_324n": {
            str(FORMAL_SCOPE_RULES_PATH): scope_hash_before,
            str(SEMANTIC_ALIAS_ASSET_PATH): alias_hash_before,
        },
        "official_assets_after_324n": {
            str(FORMAL_SCOPE_RULES_PATH): scope_hash_after,
            str(SEMANTIC_ALIAS_ASSET_PATH): alias_hash_after,
        },
        "official_assets_written": [],
        "no_official_asset_modification_during_324n": no_official_asset_modification_during_324n,
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
    warnings_df = pd.DataFrame(
        [
            {
                "warning_status": warning_status,
                "current_duplicate_count": current_duplicate_count,
                "new_duplicate_delta_count": new_duplicate_delta_count_324,
                "blocking": False,
            }
        ]
    ).fillna("")
    official_asset_proof_df = pd.DataFrame(
        [
            {
                "asset_path": str(FORMAL_SCOPE_RULES_PATH),
                "hash_before_324n": scope_hash_before,
                "hash_after_324n": scope_hash_after,
                "modified_during_324n": scope_hash_before != scope_hash_after,
            },
            {
                "asset_path": str(SEMANTIC_ALIAS_ASSET_PATH),
                "hash_before_324n": alias_hash_before,
                "hash_after_324n": alias_hash_after,
                "modified_during_324n": alias_hash_before != alias_hash_after,
            },
        ]
    ).fillna("")
    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "cached_outputs_only",
                "detail": "324N summarizes cached 324A-324M evidence and does not rerun extraction, adjudication, or semantic rules.",
            },
            {
                "limitation": "remaining_burden_not_recomputed",
                "detail": "Remaining burden metrics are inherited from 323P / pre-324 unless a later recomputation artifact is supplied.",
            },
            {
                "limitation": "historical_duplicates_unchanged",
                "detail": "current_duplicate_count remains 3, with new_duplicate_delta_count equal to 0.",
            },
        ]
    ).fillna("")

    return {
        "summary": summary,
        "qa_json": qa_json,
        "closure_json": closure_json,
        "no_apply_proof_json": no_apply_proof_json,
        "cycle_summary_df": cycle_summary_df,
        "stage_timeline_df": pd.DataFrame(stage_rows).fillna(""),
        "remaining_burden_df": remaining_burden_df,
        "warnings_df": warnings_df,
        "recommendations_df": pd.DataFrame(recommendations).fillna(""),
        "official_asset_proof_df": official_asset_proof_df,
        "qa_summary_df": qa_summary_df,
        "qa_checks_df": qa_df,
        "known_limitations_df": known_limitations_df,
    }
