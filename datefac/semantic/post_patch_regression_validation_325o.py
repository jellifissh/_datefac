from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence, Set, Tuple

import pandas as pd


EXPECTED_325N_DECISION = "OFFICIAL_ALIAS_PATCH_APPLICATION_325N_READY_FOR_325O_POST_PATCH_REGRESSION"
READY_DECISION = "POST_PATCH_REGRESSION_VALIDATION_325O_READY_FOR_325P_CYCLE_CLOSURE"
NOT_READY_DECISION = "POST_PATCH_REGRESSION_VALIDATION_325O_NOT_READY"

DEFAULT_OFFICIAL_PATCH_APPLICATION_DIR = Path(r"D:\_datefac\output\official_alias_patch_application_325n")
DEFAULT_SANDBOX_REPLAY_DIR = Path(r"D:\_datefac\output\alias_human_confirmed_sandbox_replay_325i")
DEFAULT_TRUST_SPLIT_DIR = Path(r"D:\_datefac\output\router_mineru_trust_split_322b2")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\post_patch_regression_validation_325o")

SEMANTIC_ALIAS_ASSET_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")
FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
TARGET_GROUP = "profitability"
EXPECTED_PROMOTION_STATUS = "PROMOTED_325N_OFFICIAL_PATCH"


@dataclass(frozen=True)
class AppliedAliasOperation:
    approval_record_id: str
    patch_operation_id: str
    proposal_id: str
    candidate_id: str
    normalized_alias_label: str
    target_metric: str
    target_group: str
    generated_rule_id: str
    operation_status: str
    expected_affected_candidate_count: int
    expected_trusted_gain: int
    expected_review_reduction: int
    expected_out_of_scope_or_rejected_gain: int
    source_sandbox_rule_id_325i: str


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _label_key(value: Any) -> str:
    return _norm(value).replace("\u3000", "").replace(" ", "").lower()


def _metric_key(value: Any) -> str:
    return _norm(value).replace(" ", "").lower()


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


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
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
    return rows


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "__MISSING__"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_readable(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        if path.suffix.lower() in {".json", ".jsonl", ".md", ".txt"}:
            path.read_text(encoding="utf-8")
        else:
            path.read_bytes()
    except Exception:
        return False
    return True


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


def _count_alias_duplicates(payload: Dict[str, Any]) -> int:
    seen: Set[Tuple[str, str, str]] = set()
    duplicate_count = 0
    for row in _flatten_alias_entries(payload):
        key = (
            _norm(row.get("target_group")),
            _label_key(row.get("normalized_label")),
            _metric_key(row.get("metric_code")),
        )
        if key in seen:
            duplicate_count += 1
        else:
            seen.add(key)
    return duplicate_count


def load_post_patch_regression_validation_325o_inputs(
    official_patch_application_dir: Path,
    sandbox_replay_dir: Path,
    trust_split_dir: Path,
) -> Dict[str, Any]:
    return {
        "patch_summary": _read_json(official_patch_application_dir / "official_alias_patch_application_325n_summary.json"),
        "patch_qa": _read_json(official_patch_application_dir / "official_alias_patch_application_325n_qa.json"),
        "patch_apply_proof": _read_json(official_patch_application_dir / "official_alias_patch_application_325n_apply_proof.json"),
        "patch_rollback_plan": _read_json(official_patch_application_dir / "official_alias_patch_application_325n_rollback_plan.json"),
        "patch_logs": _read_jsonl(official_patch_application_dir / "official_alias_patch_application_325n_applied_operations.jsonl"),
        "sandbox_summary": _read_json(sandbox_replay_dir / "alias_human_confirmed_sandbox_replay_325i_summary.json"),
        "sandbox_affected_rows": _read_jsonl(sandbox_replay_dir / "alias_human_confirmed_sandbox_replay_325i_affected_candidates.jsonl"),
        "trust_summary": _read_json(trust_split_dir / "router_mineru_trust_split_322b2_summary.json"),
        "alias_asset": _read_json(SEMANTIC_ALIAS_ASSET_PATH),
        "scope_asset": _read_json(FORMAL_SCOPE_RULES_PATH),
        "official_patch_application_dir": official_patch_application_dir,
        "sandbox_replay_dir": sandbox_replay_dir,
        "trust_split_dir": trust_split_dir,
    }


def _build_applied_operations(rows: Sequence[Dict[str, Any]]) -> Tuple[List[AppliedAliasOperation], List[Dict[str, Any]]]:
    operations: List[AppliedAliasOperation] = []
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    applied_or_idempotent = [
        row for row in rows
        if isinstance(row, dict) and _norm(row.get("operation_status")) in {"APPLIED", "IDEMPOTENT_ALREADY_APPLIED"}
    ]
    add("applied_operations::count", len(applied_or_idempotent) == 6, f"actual={len(applied_or_idempotent)}")

    for row in applied_or_idempotent:
        after_state = row.get("after_state")
        after_state = after_state if isinstance(after_state, dict) else {}
        operations.append(
            AppliedAliasOperation(
                approval_record_id=_norm(row.get("approval_record_id")),
                patch_operation_id=_norm(row.get("patch_operation_id")),
                proposal_id=_norm(row.get("proposal_id")),
                candidate_id=_norm(row.get("candidate_id")),
                normalized_alias_label=_norm(row.get("normalized_alias_label")) or _norm(after_state.get("normalized_label")),
                target_metric=_norm(row.get("target_metric")) or _norm(after_state.get("metric_code")),
                target_group=_norm(row.get("target_group")),
                generated_rule_id=_norm(row.get("generated_rule_id")) or _norm(after_state.get("rule_id")),
                operation_status=_norm(row.get("operation_status")),
                expected_affected_candidate_count=_safe_int(row.get("expected_affected_candidate_count")),
                expected_trusted_gain=_safe_int(row.get("expected_trusted_gain")),
                expected_review_reduction=_safe_int(row.get("expected_review_reduction")),
                expected_out_of_scope_or_rejected_gain=_safe_int(row.get("expected_out_of_scope_or_rejected_gain")),
                source_sandbox_rule_id_325i=_norm(after_state.get("source_sandbox_rule_id_325i")),
            )
        )

    add(
        "applied_operations::unique_patch_ids",
        len({row.patch_operation_id for row in operations}) == len(operations),
        f"actual={len({row.patch_operation_id for row in operations})}",
    )
    add(
        "applied_operations::unique_rule_ids",
        len({row.generated_rule_id for row in operations}) == len(operations),
        f"actual={len({row.generated_rule_id for row in operations})}",
    )

    required_failures = 0
    for row in operations:
        if not all(
            [
                row.approval_record_id,
                row.patch_operation_id,
                row.generated_rule_id,
                row.normalized_alias_label,
                row.target_metric,
                row.target_group == TARGET_GROUP,
                row.operation_status in {"APPLIED", "IDEMPOTENT_ALREADY_APPLIED"},
            ]
        ):
            required_failures += 1
    add("applied_operations::required_fields_complete", required_failures == 0, f"failed_records={required_failures}")
    return operations, checks


def _semantic_constraint_check(operation: AppliedAliasOperation) -> Tuple[bool, str]:
    allowed_by_patch_id = {
        "dry_run_325l::alias::001": {"ebit"},
        "dry_run_325l::alias::002": {"attributable_net_margin", "parent_net_margin"},
        "dry_run_325l::alias::003": {"roe"},
        "dry_run_325l::alias::004": {"diluted_eps", "eps_diluted"},
        "dry_run_325l::alias::005": {"adjusted_eps"},
        "dry_run_325l::alias::006": {
            "adjusted_attributable_net_profit",
            "adjusted_parent_net_profit",
        },
    }
    actual = _metric_key(operation.target_metric)
    allowed = allowed_by_patch_id.get(operation.patch_operation_id, set())
    if actual in allowed:
        return True, f"allowed={sorted(allowed)} actual={actual}"
    return False, f"allowed={sorted(allowed)} actual={actual}"


def build_post_patch_regression_validation_325o(
    patch_summary: Dict[str, Any],
    patch_qa: Dict[str, Any],
    patch_apply_proof: Dict[str, Any],
    patch_rollback_plan: Dict[str, Any],
    patch_logs: Sequence[Dict[str, Any]],
    sandbox_summary: Dict[str, Any],
    sandbox_affected_rows: Sequence[Dict[str, Any]],
    trust_summary: Dict[str, Any],
    alias_asset: Dict[str, Any],
    scope_asset: Dict[str, Any],
    official_patch_application_dir: Path,
    sandbox_replay_dir: Path,
    trust_split_dir: Path,
    output_dir: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(SEMANTIC_ALIAS_ASSET_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    add_qa(
        "readiness::325n_decision",
        "PASS" if _norm(patch_summary.get("decision")) == EXPECTED_325N_DECISION else "FAIL",
        _norm(patch_summary.get("decision")),
    )
    add_qa(
        "readiness::325n_summary_qa_fail_count",
        "PASS" if _safe_int(patch_summary.get("qa_fail_count")) == 0 else "FAIL",
        str(patch_summary.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::325n_qa_json_fail_count",
        "PASS" if _safe_int(patch_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(patch_qa.get("qa_fail_count", "")),
    )
    for key, expected in [
        ("applied_or_idempotent_operation_count", 6),
        ("alias_approved_patch_operation_count", 6),
        ("duplicate_delta_count", 0),
        ("target_conflict_count", 0),
        ("affected_candidate_count", 45),
        ("expected_trusted_gain", 45),
        ("expected_review_reduction", 45),
        ("expected_out_of_scope_or_rejected_gain", 0),
    ]:
        add_qa(
            f"readiness::325n_{key}",
            "PASS" if _safe_int(patch_summary.get(key)) == expected else "FAIL",
            f"expected={expected} actual={patch_summary.get(key, '')}",
        )

    operations, operation_checks = _build_applied_operations(patch_logs)
    qa_rows.extend(operation_checks)

    alias_rows = _flatten_alias_entries(alias_asset)
    profitability_rows = [row for row in alias_rows if _norm(row.get("target_group")) == TARGET_GROUP]
    visibility_rows: List[Dict[str, Any]] = []
    missing_official_alias_rule_count = 0
    wrong_target_metric_count = 0
    adjusted_metric_mismatch_count = 0
    diluted_eps_mismatch_count = 0
    semantic_failure_count = 0
    target_conflict_count_current = 0

    profitability_by_rule_id = {
        _norm(row.get("rule_id")): row
        for row in profitability_rows
        if isinstance(row, dict)
    }

    for operation in operations:
        row = profitability_by_rule_id.get(operation.generated_rule_id, {})
        visible = bool(row)
        actual_metric = _norm(row.get("metric_code"))
        target_metric_match = _metric_key(actual_metric) == _metric_key(operation.target_metric) if visible else False
        if not visible:
            missing_official_alias_rule_count += 1
        elif not target_metric_match:
            wrong_target_metric_count += 1

        label_conflict_rows = [
            item for item in profitability_rows
            if _label_key(item.get("normalized_label")) == _label_key(operation.normalized_alias_label)
            and _metric_key(item.get("metric_code")) != _metric_key(operation.target_metric)
        ]
        if label_conflict_rows:
            target_conflict_count_current += 1

        semantic_ok, semantic_detail = _semantic_constraint_check(operation)
        if not semantic_ok:
            semantic_failure_count += 1
        if operation.patch_operation_id == "dry_run_325l::alias::004" and not semantic_ok:
            diluted_eps_mismatch_count += 1
        if operation.patch_operation_id in {"dry_run_325l::alias::005", "dry_run_325l::alias::006"} and not semantic_ok:
            adjusted_metric_mismatch_count += 1

        visibility_rows.append(
            {
                "generated_rule_id": operation.generated_rule_id,
                "patch_operation_id": operation.patch_operation_id,
                "source_sandbox_rule_id_325i": operation.source_sandbox_rule_id_325i,
                "normalized_alias_label": operation.normalized_alias_label,
                "expected_target_metric": operation.target_metric,
                "actual_target_metric": actual_metric,
                "target_group": _norm(row.get("target_group")),
                "approval_stage": _norm(row.get("approval_stage")),
                "promotion_status": _norm(row.get("promotion_status")),
                "visible": visible,
                "target_metric_match": target_metric_match,
                "semantic_constraint_pass": semantic_ok,
                "semantic_constraint_detail": semantic_detail,
                "conflicting_metric_count": len(label_conflict_rows),
            }
        )
        add_qa(
            f"visibility::{operation.generated_rule_id}::present",
            "PASS" if visible else "FAIL",
            operation.generated_rule_id,
        )
        add_qa(
            f"visibility::{operation.generated_rule_id}::target_metric_match",
            "PASS" if target_metric_match else "FAIL",
            f"expected={operation.target_metric} actual={actual_metric}",
        )
        add_qa(
            f"visibility::{operation.generated_rule_id}::promotion_status",
            "PASS" if _norm(row.get("promotion_status")) == EXPECTED_PROMOTION_STATUS else "FAIL",
            _norm(row.get("promotion_status")),
        )
        add_qa(
            f"semantic::{operation.generated_rule_id}",
            "PASS" if semantic_ok else "FAIL",
            semantic_detail,
        )

    official_rule_visibility_total = sum(1 for row in visibility_rows if bool(row.get("visible")))
    official_alias_rules_visible = official_rule_visibility_total
    add_qa(
        "visibility::official_rule_visibility_total",
        "PASS" if official_rule_visibility_total == 6 else "FAIL",
        f"actual={official_rule_visibility_total}",
    )
    add_qa(
        "visibility::missing_official_alias_rule_count",
        "PASS" if missing_official_alias_rule_count == 0 else "FAIL",
        f"actual={missing_official_alias_rule_count}",
    )
    add_qa(
        "visibility::wrong_target_metric_count",
        "PASS" if wrong_target_metric_count == 0 else "FAIL",
        f"actual={wrong_target_metric_count}",
    )

    scope_hash_expected_from_325n = _norm(patch_summary.get("formal_scope_rules_hash_after")) or _norm(
        (patch_apply_proof.get("official_assets_after") or {}).get(str(FORMAL_SCOPE_RULES_PATH))
    )
    scope_hash_current = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    add_qa(
        "safety::formal_scope_rules_hash_matches_325n",
        "PASS" if scope_hash_current == scope_hash_expected_from_325n else "FAIL",
        f"expected={scope_hash_expected_from_325n} actual={scope_hash_current}",
    )

    sandbox_rows = [row for row in sandbox_affected_rows if isinstance(row, dict)]
    sandbox_by_rule_id: Dict[str, List[Dict[str, Any]]] = {}
    for row in sandbox_rows:
        sandbox_by_rule_id.setdefault(_norm(row.get("proposal_id")), []).append(row)

    impact_rows: List[Dict[str, Any]] = []
    derived_affected_candidate_count = 0
    derived_trusted_gain = 0
    derived_review_reduction = 0
    derived_out_of_scope_or_rejected_gain = 0
    core_false_mapping_count = _safe_int(sandbox_summary.get("core_false_mapping_count"))

    for operation in operations:
        rows = sandbox_by_rule_id.get(operation.source_sandbox_rule_id_325i, [])
        affected_count = len(rows)
        trusted_gain = sum(1 for row in rows if _norm(row.get("decision_after")) == "trusted_preview")
        review_reduction = sum(
            1
            for row in rows
            if _norm(row.get("decision_before")) == "review_required_preview"
            and _norm(row.get("decision_after")) != "review_required_preview"
        )
        out_of_scope_or_rejected_gain = sum(
            1
            for row in rows
            if _norm(row.get("decision_after")) in {"out_of_scope_preview", "rejected_preview"}
        )
        derived_affected_candidate_count += affected_count
        derived_trusted_gain += trusted_gain
        derived_review_reduction += review_reduction
        derived_out_of_scope_or_rejected_gain += out_of_scope_or_rejected_gain
        impact_rows.append(
            {
                "generated_rule_id": operation.generated_rule_id,
                "patch_operation_id": operation.patch_operation_id,
                "source_sandbox_rule_id_325i": operation.source_sandbox_rule_id_325i,
                "expected_affected_candidate_count": operation.expected_affected_candidate_count,
                "derived_affected_candidate_count": affected_count,
                "expected_trusted_gain": operation.expected_trusted_gain,
                "derived_trusted_gain": trusted_gain,
                "expected_review_reduction": operation.expected_review_reduction,
                "derived_review_reduction": review_reduction,
                "expected_out_of_scope_or_rejected_gain": operation.expected_out_of_scope_or_rejected_gain,
                "derived_out_of_scope_or_rejected_gain": out_of_scope_or_rejected_gain,
            }
        )
        add_qa(
            f"impact::{operation.generated_rule_id}::affected_candidate_count",
            "PASS" if affected_count == operation.expected_affected_candidate_count else "FAIL",
            f"expected={operation.expected_affected_candidate_count} actual={affected_count}",
        )
        add_qa(
            f"impact::{operation.generated_rule_id}::trusted_gain",
            "PASS" if trusted_gain == operation.expected_trusted_gain else "FAIL",
            f"expected={operation.expected_trusted_gain} actual={trusted_gain}",
        )
        add_qa(
            f"impact::{operation.generated_rule_id}::review_reduction",
            "PASS" if review_reduction == operation.expected_review_reduction else "FAIL",
            f"expected={operation.expected_review_reduction} actual={review_reduction}",
        )
        add_qa(
            f"impact::{operation.generated_rule_id}::out_of_scope_or_rejected_gain",
            "PASS" if out_of_scope_or_rejected_gain == operation.expected_out_of_scope_or_rejected_gain else "FAIL",
            f"expected={operation.expected_out_of_scope_or_rejected_gain} actual={out_of_scope_or_rejected_gain}",
        )

    affected_candidate_count = _safe_int(sandbox_summary.get("affected_candidate_count"))
    trusted_gain_325o = _safe_int(sandbox_summary.get("trusted_gain_325i"))
    review_reduction_325o = _safe_int(sandbox_summary.get("review_reduction_325i"))
    out_of_scope_or_rejected_gain_325o = _safe_int(sandbox_summary.get("out_of_scope_or_rejected_gain_325i"))
    for name, actual, expected in [
        ("affected_candidate_count", affected_candidate_count, 45),
        ("trusted_gain_325o", trusted_gain_325o, 45),
        ("review_reduction_325o", review_reduction_325o, 45),
        ("out_of_scope_or_rejected_gain_325o", out_of_scope_or_rejected_gain_325o, 0),
    ]:
        add_qa(f"impact::{name}", "PASS" if actual == expected else "FAIL", f"expected={expected} actual={actual}")
    add_qa(
        "impact::derived_affected_candidate_count",
        "PASS" if derived_affected_candidate_count == 45 else "FAIL",
        f"actual={derived_affected_candidate_count}",
    )
    add_qa(
        "impact::derived_trusted_gain",
        "PASS" if derived_trusted_gain == 45 else "FAIL",
        f"actual={derived_trusted_gain}",
    )
    add_qa(
        "impact::derived_review_reduction",
        "PASS" if derived_review_reduction == 45 else "FAIL",
        f"actual={derived_review_reduction}",
    )
    add_qa(
        "impact::derived_out_of_scope_or_rejected_gain",
        "PASS" if derived_out_of_scope_or_rejected_gain == 0 else "FAIL",
        f"actual={derived_out_of_scope_or_rejected_gain}",
    )

    current_duplicate_count = _count_alias_duplicates(alias_asset)
    duplicate_delta_count = current_duplicate_count - _safe_int(patch_summary.get("duplicate_count_after"))
    add_qa(
        "duplicates::current_duplicate_count",
        "PASS" if current_duplicate_count == _safe_int(patch_summary.get("duplicate_count_after")) else "FAIL",
        f"expected={patch_summary.get('duplicate_count_after', '')} actual={current_duplicate_count}",
    )
    add_qa(
        "duplicates::duplicate_delta_count",
        "PASS" if duplicate_delta_count == 0 else "FAIL",
        f"delta={duplicate_delta_count}",
    )
    add_qa(
        "conflicts::target_conflict_count",
        "PASS" if target_conflict_count_current == 0 else "FAIL",
        f"actual={target_conflict_count_current}",
    )
    add_qa(
        "semantic::adjusted_metric_mismatch_count",
        "PASS" if adjusted_metric_mismatch_count == 0 else "FAIL",
        f"actual={adjusted_metric_mismatch_count}",
    )
    add_qa(
        "semantic::diluted_eps_mismatch_count",
        "PASS" if diluted_eps_mismatch_count == 0 else "FAIL",
        f"actual={diluted_eps_mismatch_count}",
    )
    add_qa(
        "semantic::core_false_mapping_count",
        "PASS" if core_false_mapping_count == 0 else "FAIL",
        f"actual={core_false_mapping_count}",
    )

    rollback_rows = patch_rollback_plan.get("rollback_rows", [])
    rollback_rows = rollback_rows if isinstance(rollback_rows, list) else []
    rollback_artifacts = [
        ("summary_json", official_patch_application_dir / "official_alias_patch_application_325n_summary.json"),
        ("qa_json", official_patch_application_dir / "official_alias_patch_application_325n_qa.json"),
        ("apply_proof_json", official_patch_application_dir / "official_alias_patch_application_325n_apply_proof.json"),
        ("rollback_plan_json", official_patch_application_dir / "official_alias_patch_application_325n_rollback_plan.json"),
        ("rollback_instructions_md", official_patch_application_dir / "official_alias_patch_application_325n_rollback_instructions.md"),
        ("alias_backup_json", Path((patch_summary.get("rollback_backup_paths") or {}).get("alias_backup_path", ""))),
    ]
    rollback_artifact_rows: List[Dict[str, Any]] = []
    for artifact_name, path in rollback_artifacts:
        exists = path.exists()
        readable = _artifact_readable(path)
        rollback_artifact_rows.append(
            {"artifact_name": artifact_name, "path": str(path), "exists": exists, "readable": readable}
        )
        add_qa(
            f"rollback::{artifact_name}_present_and_readable",
            "PASS" if exists and readable else "FAIL",
            str(path),
        )
    rollback_artifact_check_passed = bool(
        all(row["exists"] and row["readable"] for row in rollback_artifact_rows)
    ) and len(rollback_rows) == 6
    add_qa(
        "rollback::rollback_row_count",
        "PASS" if len(rollback_rows) == 6 else "FAIL",
        f"actual={len(rollback_rows)}",
    )

    trust_summary_loaded = bool(trust_summary)
    add_qa("reference::trust_split_summary_loaded", "PASS" if trust_summary_loaded else "FAIL", str(trust_split_dir))

    alias_hash_after = _sha256_file(SEMANTIC_ALIAS_ASSET_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    no_official_asset_modification_during_325o = (
        alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after
    )
    add_qa(
        "safety::no_official_asset_modification_during_325o",
        "PASS" if no_official_asset_modification_during_325o else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )
    add_qa("safety::no_llm_or_production_apply", "PASS", "325O uses cached evidence and reads official assets only.")

    visibility_df = pd.DataFrame(visibility_rows).fillna("")
    impact_df = pd.DataFrame(impact_rows).fillna("")
    duplicate_conflict_df = pd.DataFrame(
        [
            {
                "current_duplicate_count": current_duplicate_count,
                "duplicate_delta_count": duplicate_delta_count,
                "target_conflict_count": target_conflict_count_current,
                "wrong_target_metric_count": wrong_target_metric_count,
                "missing_official_alias_rule_count": missing_official_alias_rule_count,
                "semantic_failure_count": semantic_failure_count,
                "adjusted_metric_mismatch_count": adjusted_metric_mismatch_count,
                "diluted_eps_mismatch_count": diluted_eps_mismatch_count,
                "core_false_mapping_count": core_false_mapping_count,
            }
        ]
    ).fillna("")
    rollback_artifact_df = pd.DataFrame(rollback_artifact_rows).fillna("")
    before_after_df = pd.DataFrame(
        [
            {
                "asset_path": str(SEMANTIC_ALIAS_ASSET_PATH),
                "hash_before_325o": alias_hash_before,
                "hash_after_325o": alias_hash_after,
                "modified_during_325o": alias_hash_before != alias_hash_after,
            },
            {
                "asset_path": str(FORMAL_SCOPE_RULES_PATH),
                "hash_before_325o": scope_hash_before,
                "hash_after_325o": scope_hash_after,
                "modified_during_325o": scope_hash_before != scope_hash_after,
            },
        ]
    ).fillna("")
    semantic_constraint_df = pd.DataFrame(
        [
            {
                "generated_rule_id": row["generated_rule_id"],
                "patch_operation_id": row["patch_operation_id"],
                "normalized_alias_label": row["normalized_alias_label"],
                "expected_target_metric": row["expected_target_metric"],
                "semantic_constraint_pass": row["semantic_constraint_pass"],
                "semantic_constraint_detail": row["semantic_constraint_detail"],
            }
            for row in visibility_rows
        ]
    ).fillna("")

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    summary = {
        "stage": "325O",
        "output_dir": str(output_dir),
        "official_rule_visibility_total": official_rule_visibility_total,
        "official_alias_rules_visible": official_alias_rules_visible,
        "missing_official_alias_rule_count": missing_official_alias_rule_count,
        "wrong_target_metric_count": wrong_target_metric_count,
        "affected_candidate_count": affected_candidate_count,
        "trusted_gain_325o": trusted_gain_325o,
        "review_reduction_325o": review_reduction_325o,
        "out_of_scope_or_rejected_gain_325o": out_of_scope_or_rejected_gain_325o,
        "current_duplicate_count": current_duplicate_count,
        "duplicate_delta_count": duplicate_delta_count,
        "target_conflict_count": target_conflict_count_current,
        "adjusted_metric_mismatch_count": adjusted_metric_mismatch_count,
        "diluted_eps_mismatch_count": diluted_eps_mismatch_count,
        "core_false_mapping_count": core_false_mapping_count,
        "rollback_artifact_check_passed": rollback_artifact_check_passed,
        "formal_scope_rules_hash_matches_325n": scope_hash_current == scope_hash_expected_from_325n,
        "no_official_asset_modification_during_325o": no_official_asset_modification_during_325o,
        "trust_split_summary_loaded": trust_summary_loaded,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION,
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
        "official_alias_rules_visible": official_alias_rules_visible,
        "missing_official_alias_rule_count": missing_official_alias_rule_count,
        "wrong_target_metric_count": wrong_target_metric_count,
        "visibility_records": visibility_df.to_dict(orient="records"),
    }
    rollback_artifact_check_json = {
        "rollback_artifact_check_passed": rollback_artifact_check_passed,
        "artifacts": rollback_artifact_df.to_dict(orient="records"),
        "rollback_row_count": len(rollback_rows),
    }
    no_apply_proof_json = {
        "stage": "325O",
        "decision": summary["decision"],
        "files_read": [
            str(official_patch_application_dir / "official_alias_patch_application_325n_summary.json"),
            str(official_patch_application_dir / "official_alias_patch_application_325n_qa.json"),
            str(official_patch_application_dir / "official_alias_patch_application_325n_apply_proof.json"),
            str(official_patch_application_dir / "official_alias_patch_application_325n_rollback_plan.json"),
            str(official_patch_application_dir / "official_alias_patch_application_325n_applied_operations.jsonl"),
            str(sandbox_replay_dir / "alias_human_confirmed_sandbox_replay_325i_summary.json"),
            str(sandbox_replay_dir / "alias_human_confirmed_sandbox_replay_325i_affected_candidates.jsonl"),
            str(trust_split_dir / "router_mineru_trust_split_322b2_summary.json"),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
        "official_assets_before_325o": {
            str(SEMANTIC_ALIAS_ASSET_PATH): alias_hash_before,
            str(FORMAL_SCOPE_RULES_PATH): scope_hash_before,
        },
        "official_assets_after_325o": {
            str(SEMANTIC_ALIAS_ASSET_PATH): alias_hash_after,
            str(FORMAL_SCOPE_RULES_PATH): scope_hash_after,
        },
        "official_assets_written": [],
        "no_official_asset_modification_during_325o": no_official_asset_modification_during_325o,
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
                "limitation": "cached_evidence_only",
                "detail": "325O validates 325N alias visibility and reproduces impact from cached 325I replay evidence only.",
            },
            {
                "limitation": "official_assets_read_only",
                "detail": "325O proves no official asset modification by comparing before and after hashes in the same run.",
            },
            {
                "limitation": "official_rule_subset_only",
                "detail": "325O processes only the six alias rules applied by 325N.",
            },
        ]
    ).fillna("")

    return {
        "summary": summary,
        "qa_json": qa_json,
        "visibility_json": visibility_json,
        "rollback_artifact_check_json": rollback_artifact_check_json,
        "no_apply_proof_json": no_apply_proof_json,
        "visibility_df": visibility_df,
        "impact_df": impact_df,
        "duplicate_conflict_df": duplicate_conflict_df,
        "rollback_artifact_df": rollback_artifact_df,
        "before_after_df": before_after_df,
        "semantic_constraint_df": semantic_constraint_df,
        "qa_summary_df": qa_summary_df,
        "qa_checks_df": qa_df,
        "known_limitations_df": known_limitations_df,
    }
