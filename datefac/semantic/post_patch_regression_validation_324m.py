from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import pandas as pd


EXPECTED_324L_DECISION = "OFFICIAL_PATCH_APPLICATION_324L_READY_FOR_324M_POST_PATCH_REGRESSION"
READY_DECISION = "POST_PATCH_REGRESSION_VALIDATION_324M_READY_TO_CLOSE_324_SCOPE_PATCH_CYCLE"
READY_WITH_WARNINGS_DECISION = "POST_PATCH_REGRESSION_VALIDATION_324M_READY_WITH_WARNINGS"
NOT_READY_DECISION = "POST_PATCH_REGRESSION_VALIDATION_324M_NOT_READY"

DEFAULT_OFFICIAL_PATCH_APPLICATION_DIR = Path(r"D:\_datefac\output\official_patch_application_324l")
DEFAULT_SANDBOX_REPLAY_DIR = Path(r"D:\_datefac\output\scope_noise_human_confirmed_sandbox_replay_324g")
DEFAULT_TRUST_SPLIT_DIR = Path(r"D:\_datefac\output\router_mineru_trust_split_322b2")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\post_patch_regression_validation_324m")

FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
SEMANTIC_ALIAS_ASSET_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")

EXPECTED_RULE_ID = "SEM_SCOPE_324L_001"
EXPECTED_TARGET_GROUP = "core_metric_scope_exclusions"
EXPECTED_SCOPE_ACTION = "exclude_from_core_metric_mapping"
EXPECTED_PROMOTION_STATUS = "PROMOTED_324L_OFFICIAL_PATCH"
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


def _flatten_scope_entries(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    rules = payload.get("rules", {}) if isinstance(payload, dict) else {}
    rows: List[Dict[str, Any]] = []
    if not isinstance(rules, dict):
        return rows
    for rule_id, item in rules.items():
        if not isinstance(item, dict):
            continue
        row = dict(item)
        row.setdefault("rule_id", _norm(rule_id))
        rows.append(row)
    return rows


def _flatten_alias_entries(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    groups = payload.get("groups", {}) if isinstance(payload, dict) else {}
    rows: List[Dict[str, Any]] = []
    if not isinstance(groups, dict):
        return rows
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


def _count_scope_duplicates(payload: Dict[str, Any]) -> int:
    seen: Set[Tuple[str, str, str]] = set()
    duplicate_count = 0
    for row in _flatten_scope_entries(payload):
        key = (
            _norm(row.get("target_group")),
            _normalize_label(row.get("normalized_label")),
            _norm(row.get("scope_action")),
        )
        if key in seen:
            duplicate_count += 1
        else:
            seen.add(key)
    return duplicate_count


def _count_alias_duplicates(payload: Dict[str, Any]) -> int:
    seen: Set[Tuple[str, str, str]] = set()
    duplicate_count = 0
    for row in _flatten_alias_entries(payload):
        key = (
            _norm(row.get("target_group")),
            _normalize_label(row.get("normalized_label")),
            _norm(row.get("metric_code")),
        )
        if key in seen:
            duplicate_count += 1
        else:
            seen.add(key)
    return duplicate_count


def _artifact_readable(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        if path.suffix.lower() in {".json", ".md", ".txt"}:
            path.read_text(encoding="utf-8")
        else:
            path.read_bytes()
    except Exception:
        return False
    return True


def load_post_patch_regression_validation_324m_inputs(
    official_patch_application_dir: Path,
    sandbox_replay_dir: Path,
    trust_split_dir: Path,
) -> Dict[str, Any]:
    return {
        "patch_summary": _read_json(official_patch_application_dir / "official_patch_application_324l_summary.json"),
        "patch_qa": _read_json(official_patch_application_dir / "official_patch_application_324l_qa.json"),
        "patch_apply_proof": _read_json(official_patch_application_dir / "official_patch_application_324l_apply_proof.json"),
        "patch_rollback_plan": _read_json(official_patch_application_dir / "official_patch_application_324l_rollback_plan.json"),
        "sandbox_summary": _read_json(sandbox_replay_dir / "scope_noise_human_confirmed_sandbox_replay_324g_summary.json"),
        "trust_summary": _read_json(trust_split_dir / "router_mineru_trust_split_322b2_summary.json"),
        "scope_asset": _read_json(FORMAL_SCOPE_RULES_PATH),
        "alias_asset": _read_json(SEMANTIC_ALIAS_ASSET_PATH),
        "official_patch_application_dir": official_patch_application_dir,
        "sandbox_replay_dir": sandbox_replay_dir,
        "trust_split_dir": trust_split_dir,
    }


def _determine_decision(qa_df: pd.DataFrame) -> str:
    if qa_df.empty:
        return NOT_READY_DECISION
    fail_count = int((qa_df["status"] == "FAIL").sum())
    warn_names = set(qa_df.loc[qa_df["status"] == "WARN", "check_name"].astype(str).tolist())
    if fail_count > 0:
        return NOT_READY_DECISION
    if warn_names and warn_names.issubset({HISTORICAL_DUPLICATE_WARNING_CHECK}):
        return READY_WITH_WARNINGS_DECISION
    if warn_names:
        return NOT_READY_DECISION
    return READY_DECISION


def build_post_patch_regression_validation_324m(
    patch_summary: Dict[str, Any],
    patch_qa: Dict[str, Any],
    patch_apply_proof: Dict[str, Any],
    patch_rollback_plan: Dict[str, Any],
    sandbox_summary: Dict[str, Any],
    trust_summary: Dict[str, Any],
    scope_asset: Dict[str, Any],
    alias_asset: Dict[str, Any],
    official_patch_application_dir: Path,
    sandbox_replay_dir: Path,
    trust_split_dir: Path,
    output_dir: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    alias_hash_before = _sha256_file(SEMANTIC_ALIAS_ASSET_PATH)

    add_qa("readiness::324l_decision", "PASS" if _norm(patch_summary.get("decision")) == EXPECTED_324L_DECISION else "FAIL", _norm(patch_summary.get("decision")))
    add_qa("readiness::324l_summary_qa_fail_count", "PASS" if _safe_int(patch_summary.get("qa_fail_count")) == 0 else "FAIL", str(patch_summary.get("qa_fail_count", "")))
    add_qa("readiness::324l_qa_json_fail_count", "PASS" if _safe_int(patch_qa.get("qa_fail_count")) == 0 else "FAIL", str(patch_qa.get("qa_fail_count", "")))
    for key, expected in [
        ("approved_patch_operation_count", 1),
        ("scope_approved_patch_operation_count", 1),
        ("alias_approved_patch_operation_count", 0),
        ("applied_or_idempotent_operation_count", 1),
        ("expected_review_reduction", 42),
        ("expected_out_of_scope_or_rejected_gain", 42),
        ("expected_trusted_gain", 0),
    ]:
        add_qa(f"readiness::324l_{key}", "PASS" if _safe_int(patch_summary.get(key)) == expected else "FAIL", f"expected={expected} actual={patch_summary.get(key, '')}")

    scope_entries = _flatten_scope_entries(scope_asset)
    alias_entries = _flatten_alias_entries(alias_asset)
    visible_rule = next((row for row in scope_entries if _norm(row.get("rule_id")) == EXPECTED_RULE_ID), {})
    visibility_rows = [
        {
            "rule_id": _norm(visible_rule.get("rule_id")),
            "rule_type": _norm(visible_rule.get("rule_type")),
            "target_group": _norm(visible_rule.get("target_group")),
            "scope_action": _norm(visible_rule.get("scope_action")),
            "promotion_status": _norm(visible_rule.get("promotion_status")),
            "normalized_label": _norm(visible_rule.get("normalized_label")),
            "visible": bool(visible_rule),
            "visibility_source": str(FORMAL_SCOPE_RULES_PATH),
        }
    ]
    visibility_df = pd.DataFrame(visibility_rows).fillna("")

    official_rule_visibility_total = 1 if visible_rule else 0
    scope_rules_visible = 1 if visible_rule else 0
    alias_rules_visible = 0
    add_qa("visibility::rule_present", "PASS" if visible_rule else "FAIL", EXPECTED_RULE_ID)
    add_qa("visibility::target_group", "PASS" if _norm(visible_rule.get("target_group")) == EXPECTED_TARGET_GROUP else "FAIL", _norm(visible_rule.get("target_group")))
    add_qa("visibility::scope_action", "PASS" if _norm(visible_rule.get("scope_action")) == EXPECTED_SCOPE_ACTION else "FAIL", _norm(visible_rule.get("scope_action")))
    add_qa("visibility::promotion_status", "PASS" if _norm(visible_rule.get("promotion_status")) == EXPECTED_PROMOTION_STATUS else "FAIL", _norm(visible_rule.get("promotion_status")))

    proof_before = patch_apply_proof.get("official_assets_before", {})
    proof_after = patch_apply_proof.get("official_assets_after", {})
    alias_proof_before = _norm(proof_before.get(str(SEMANTIC_ALIAS_ASSET_PATH)))
    alias_proof_after = _norm(proof_after.get(str(SEMANTIC_ALIAS_ASSET_PATH)))
    alias_hash_current = _sha256_file(SEMANTIC_ALIAS_ASSET_PATH)
    alias_unchanged_from_324l = alias_proof_before == alias_proof_after == alias_hash_current
    add_qa(
        "safety::alias_asset_unchanged_from_324l_hash_proof",
        "PASS" if alias_unchanged_from_324l else "FAIL",
        f"proof_before={alias_proof_before} proof_after={alias_proof_after} current={alias_hash_current}",
    )

    affected_candidate_count = _safe_int(sandbox_summary.get("affected_candidate_count"))
    trusted_gain_324m = _safe_int(sandbox_summary.get("trusted_gain_324g"))
    review_reduction_324m = _safe_int(sandbox_summary.get("review_reduction_324g"))
    out_of_scope_or_rejected_gain_324m = _safe_int(sandbox_summary.get("out_of_scope_or_rejected_gain_324g"))
    for name, actual, expected in [
        ("affected_candidate_count", affected_candidate_count, 42),
        ("trusted_gain_324m", trusted_gain_324m, 0),
        ("review_reduction_324m", review_reduction_324m, 42),
        ("out_of_scope_or_rejected_gain_324m", out_of_scope_or_rejected_gain_324m, 42),
    ]:
        add_qa(f"impact::{name}", "PASS" if actual == expected else "FAIL", f"expected={expected} actual={actual}")

    core_false_exclusion_count = _safe_int(sandbox_summary.get("core_false_exclusion_count"))
    add_qa("safety::core_false_exclusion_count", "PASS" if core_false_exclusion_count == 0 else "FAIL", f"actual={core_false_exclusion_count}")

    historical_duplicate_count = _safe_int(patch_summary.get("duplicate_count_before"))
    current_duplicate_count = _count_alias_duplicates(alias_asset) + _count_scope_duplicates(scope_asset)
    new_duplicate_delta_count = current_duplicate_count - historical_duplicate_count
    add_qa(
        "duplicates::new_duplicate_delta_count",
        "PASS" if new_duplicate_delta_count == 0 else "FAIL",
        f"historical={historical_duplicate_count} current={current_duplicate_count} delta={new_duplicate_delta_count}",
    )
    if current_duplicate_count > 0 and new_duplicate_delta_count == 0:
        add_qa(HISTORICAL_DUPLICATE_WARNING_CHECK, "WARN", f"historical_duplicate_count={current_duplicate_count}")

    duplicate_visible_rule_id_count = 0
    visible_rule_ids = [row.get("rule_id", "") for row in scope_entries if _norm(row.get("rule_id")) == EXPECTED_RULE_ID]
    if len(visible_rule_ids) > len(set(visible_rule_ids)):
        duplicate_visible_rule_id_count = len(visible_rule_ids) - len(set(visible_rule_ids))
    alias_labels = {_normalize_label(row.get("normalized_label")) for row in alias_entries}
    scope_label = _normalize_label(visible_rule.get("normalized_label"))
    alias_scope_label_conflict_count = 1 if scope_label and scope_label in alias_labels else 0
    conflict_count = duplicate_visible_rule_id_count + alias_scope_label_conflict_count
    add_qa("conflicts::visible_rule_id_duplicates", "PASS" if duplicate_visible_rule_id_count == 0 else "FAIL", f"actual={duplicate_visible_rule_id_count}")
    add_qa("conflicts::alias_scope_label_conflicts", "PASS" if alias_scope_label_conflict_count == 0 else "FAIL", f"actual={alias_scope_label_conflict_count}")

    rollback_artifacts = [
        ("rollback_plan_json", official_patch_application_dir / "official_patch_application_324l_rollback_plan.json"),
        ("rollback_instructions_md", official_patch_application_dir / "official_patch_application_324l_rollback_instructions.md"),
        ("scope_backup_json", Path((patch_summary.get("rollback_backup_paths") or {}).get("scope_backup_path", ""))),
    ]
    rollback_rows: List[Dict[str, Any]] = []
    for artifact_name, path in rollback_artifacts:
        exists = path.exists()
        readable = _artifact_readable(path)
        rollback_rows.append({"artifact_name": artifact_name, "path": str(path), "exists": exists, "readable": readable})
        add_qa(f"rollback::{artifact_name}_present_and_readable", "PASS" if exists and readable else "FAIL", str(path))
    rollback_artifact_df = pd.DataFrame(rollback_rows).fillna("")
    rollback_artifact_check_passed = bool(
        (rollback_artifact_df["exists"] & rollback_artifact_df["readable"]).all()
    ) if not rollback_artifact_df.empty else False

    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    alias_hash_after = _sha256_file(SEMANTIC_ALIAS_ASSET_PATH)
    no_official_asset_modification_during_324m = (
        scope_hash_before == scope_hash_after and alias_hash_before == alias_hash_after
    )
    add_qa(
        "safety::no_official_asset_modification_during_324m",
        "PASS" if no_official_asset_modification_during_324m else "FAIL",
        f"scope_before={scope_hash_before} scope_after={scope_hash_after} alias_before={alias_hash_before} alias_after={alias_hash_after}",
    )
    add_qa("safety::no_parser_or_llm_run", "PASS", "324M uses cached evidence and official asset reads only.")

    duplicate_conflict_df = pd.DataFrame(
        [
            {
                "historical_duplicate_count": historical_duplicate_count,
                "current_duplicate_count": current_duplicate_count,
                "new_duplicate_delta_count": new_duplicate_delta_count,
                "duplicate_visible_rule_id_count": duplicate_visible_rule_id_count,
                "alias_scope_label_conflict_count": alias_scope_label_conflict_count,
                "conflict_count": conflict_count,
            }
        ]
    ).fillna("")
    impact_df = pd.DataFrame(
        [
            {
                "rule_id": EXPECTED_RULE_ID,
                "affected_candidate_count": affected_candidate_count,
                "trusted_gain_324m": trusted_gain_324m,
                "review_reduction_324m": review_reduction_324m,
                "out_of_scope_or_rejected_gain_324m": out_of_scope_or_rejected_gain_324m,
                "source_sandbox_summary": str(sandbox_replay_dir / "scope_noise_human_confirmed_sandbox_replay_324g_summary.json"),
            }
        ]
    ).fillna("")
    core_false_exclusion_df = pd.DataFrame(
        [
            {
                "rule_id": EXPECTED_RULE_ID,
                "core_false_exclusion_count": core_false_exclusion_count,
                "check_result": "PASS" if core_false_exclusion_count == 0 else "FAIL",
            }
        ]
    ).fillna("")
    before_after_df = pd.DataFrame(
        [
            {
                "asset_path": str(FORMAL_SCOPE_RULES_PATH),
                "hash_before_324m": scope_hash_before,
                "hash_after_324m": scope_hash_after,
                "modified_during_324m": scope_hash_before != scope_hash_after,
            },
            {
                "asset_path": str(SEMANTIC_ALIAS_ASSET_PATH),
                "hash_before_324m": alias_hash_before,
                "hash_after_324m": alias_hash_after,
                "modified_during_324m": alias_hash_before != alias_hash_after,
            },
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
        "stage": "324M",
        "output_dir": str(output_dir),
        "official_rule_visibility_total": official_rule_visibility_total,
        "scope_rules_visible": scope_rules_visible,
        "alias_rules_visible": alias_rules_visible,
        "affected_candidate_count": affected_candidate_count,
        "trusted_gain_324m": trusted_gain_324m,
        "review_reduction_324m": review_reduction_324m,
        "out_of_scope_or_rejected_gain_324m": out_of_scope_or_rejected_gain_324m,
        "core_false_exclusion_count": core_false_exclusion_count,
        "historical_duplicate_count": historical_duplicate_count,
        "current_duplicate_count": current_duplicate_count,
        "new_duplicate_delta_count": new_duplicate_delta_count,
        "conflict_count": conflict_count,
        "rollback_artifact_check_passed": rollback_artifact_check_passed,
        "alias_official_asset_unchanged_confirmed": alias_unchanged_from_324l,
        "no_official_asset_modification_during_324m": no_official_asset_modification_during_324m,
        "trust_split_summary_loaded": bool(trust_summary),
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
    visibility_json = {
        "official_rule_visibility_total": official_rule_visibility_total,
        "scope_rules_visible": scope_rules_visible,
        "alias_rules_visible": alias_rules_visible,
        "expected_rule_id": EXPECTED_RULE_ID,
        "visibility_records": visibility_df.to_dict(orient="records"),
    }
    duplicate_conflict_json = duplicate_conflict_df.to_dict(orient="records")[0]
    rollback_artifact_check_json = {
        "rollback_artifact_check_passed": rollback_artifact_check_passed,
        "artifacts": rollback_artifact_df.to_dict(orient="records"),
    }
    no_apply_proof_json = {
        "stage": "324M",
        "decision": decision,
        "files_read": [
            str(official_patch_application_dir / "official_patch_application_324l_summary.json"),
            str(official_patch_application_dir / "official_patch_application_324l_qa.json"),
            str(official_patch_application_dir / "official_patch_application_324l_apply_proof.json"),
            str(official_patch_application_dir / "official_patch_application_324l_rollback_plan.json"),
            str(sandbox_replay_dir / "scope_noise_human_confirmed_sandbox_replay_324g_summary.json"),
            str(trust_split_dir / "router_mineru_trust_split_322b2_summary.json"),
            str(FORMAL_SCOPE_RULES_PATH),
            str(SEMANTIC_ALIAS_ASSET_PATH),
        ],
        "official_assets_before_324m": {
            str(FORMAL_SCOPE_RULES_PATH): scope_hash_before,
            str(SEMANTIC_ALIAS_ASSET_PATH): alias_hash_before,
        },
        "official_assets_after_324m": {
            str(FORMAL_SCOPE_RULES_PATH): scope_hash_after,
            str(SEMANTIC_ALIAS_ASSET_PATH): alias_hash_after,
        },
        "official_assets_written": [],
        "no_official_asset_modification_during_324m": no_official_asset_modification_during_324m,
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
                "limitation": "cached_evidence_only",
                "detail": "324M validates the 324L rule using 324L proof, 324G cached replay metrics, and current official asset reads only.",
            },
            {
                "limitation": "historical_duplicates_may_remain",
                "detail": "Historical duplicate count may remain as a warning when no new duplicate delta is introduced.",
            },
            {
                "limitation": "read_only_official_assets",
                "detail": "324M proves official assets were not modified by comparing before/after hashes in the same run.",
            },
        ]
    ).fillna("")

    return {
        "summary": summary,
        "qa_json": qa_json,
        "visibility_json": visibility_json,
        "duplicate_conflict_json": duplicate_conflict_json,
        "rollback_artifact_check_json": rollback_artifact_check_json,
        "no_apply_proof_json": no_apply_proof_json,
        "visibility_df": visibility_df,
        "impact_df": impact_df,
        "core_false_exclusion_df": core_false_exclusion_df,
        "duplicate_conflict_df": duplicate_conflict_df,
        "rollback_artifact_df": rollback_artifact_df,
        "before_after_df": before_after_df,
        "qa_summary_df": qa_summary_df,
        "qa_checks_df": qa_df,
        "known_limitations_df": known_limitations_df,
    }
