from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import pandas as pd


EXPECTED_324K_REVIEWED_DECISION = (
    "CONTROLLED_OFFICIAL_PROPOSAL_HUMAN_APPROVAL_324K_REVIEWED_READY_FOR_324L_OFFICIAL_PATCH_APPLICATION"
)
EXPECTED_324J_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_DRY_RUN_324J_READY_WITH_WARNINGS"
EXPECTED_324L_DECISION = "OFFICIAL_PATCH_APPLICATION_324L_READY_FOR_324M_POST_PATCH_REGRESSION"
EXPECTED_324L_NOT_READY = "OFFICIAL_PATCH_APPLICATION_324L_NOT_READY"

DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\official_patch_application_324l")
FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
SEMANTIC_ALIAS_ASSET_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")
SCOPE_TARGET_GROUP = "core_metric_scope_exclusions"
SCOPE_ACTION = "exclude_from_core_metric_mapping"


@dataclass(frozen=True)
class ApprovedOperation:
    approval_id: str
    reviewer_decision: str
    reviewer_name: str
    reviewer_note: str
    approval_timestamp: str
    dry_run_patch_operation_id: str
    controlled_proposal_id_324i: str
    source_rule_candidate_id_324h: str
    candidate_type: str
    patch_operation_type: str
    proposal_type: str
    target_asset_path: str
    target_group_name: str
    target_locator: str
    normalized_label: str
    proposed_change: Dict[str, Any]
    expected_affected_candidate_count: int
    expected_trusted_gain: int
    expected_review_reduction: int
    expected_out_of_scope_or_rejected_gain: int
    source_candidate_ids_324a: str
    source_review_ids_324b: str
    source_request_ids_324c: str
    source_response_ids_324d: str
    source_validation_ids_324e: str
    source_confirmation_ids_324f: str
    source_sandbox_rule_ids_324g: str
    provenance: str
    dry_run_evidence: str
    rollback_note: str
    warning_notes: str
    risk_flags: str
    generated_rule_id: str
    scope_action: str


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


def _parse_json(value: Any) -> Dict[str, Any]:
    text = _norm(value)
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


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


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def _generated_rule_id(approval_id: str) -> str:
    suffix = _norm(approval_id).split("::")[-1] or "001"
    return f"SEM_SCOPE_324L_{suffix}"


def _load_scope_asset() -> Dict[str, Any]:
    payload = _read_json(FORMAL_SCOPE_RULES_PATH)
    if not payload:
        return {
            "schema_version": "1.0",
            "rule_family": "formal_scope_rules",
            "description": "Formal scope applicability rules for financial standardization.",
            "rules": {},
        }
    rules = payload.get("rules", {})
    if not isinstance(rules, dict):
        rules = {}
    payload["rules"] = rules
    payload.setdefault("schema_version", "1.0")
    payload.setdefault("rule_family", "formal_scope_rules")
    payload.setdefault(
        "description",
        "Formal scope applicability rules for financial standardization.",
    )
    return payload


def _write_scope_asset(payload: Dict[str, Any]) -> None:
    rules = payload.get("rules", {})
    if not isinstance(rules, dict):
        rules = {}
    output = {
        "schema_version": payload.get("schema_version", "1.0"),
        "rule_family": payload.get("rule_family", "formal_scope_rules"),
        "description": payload.get(
            "description",
            "Formal scope applicability rules for financial standardization.",
        ),
        "rules": {rule_id: rules[rule_id] for rule_id in sorted(rules.keys())},
    }
    FORMAL_SCOPE_RULES_PATH.write_text(
        json.dumps(_to_jsonable(output), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _load_alias_asset() -> Dict[str, Any]:
    payload = _read_json(SEMANTIC_ALIAS_ASSET_PATH)
    if not payload:
        return {
            "schema_version": "1.0",
            "rule_family": "semantic_alias_candidates",
            "description": "Official semantic alias candidates approved for controlled semantic mapping.",
            "groups": {},
        }
    groups = payload.get("groups", {})
    if not isinstance(groups, dict):
        groups = {}
    payload["groups"] = groups
    return payload


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


def _count_scope_duplicates(payload: Dict[str, Any]) -> int:
    seen: set[Tuple[str, str, str]] = set()
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


def _snapshot_asset(path: Path, asset_type: str) -> Dict[str, Any]:
    if asset_type == "alias":
        payload = _load_alias_asset()
        groups = payload.get("groups", {})
        group_counts = {
            _norm(group_name): len(items)
            for group_name, items in groups.items()
            if isinstance(items, list)
        } if isinstance(groups, dict) else {}
        return {
            "asset_type": "alias",
            "path": str(path),
            "file_exists": path.exists(),
            "content_hash": _sha256_file(path),
            "rule_family": _norm(payload.get("rule_family")),
            "group_counts": group_counts,
            "entry_count": int(sum(group_counts.values())),
        }

    payload = _load_scope_asset()
    entries = _flatten_scope_entries(payload)
    group_counts: Dict[str, int] = {}
    for row in entries:
        group_name = _norm(row.get("target_group"))
        group_counts[group_name] = group_counts.get(group_name, 0) + 1
    return {
        "asset_type": "scope",
        "path": str(path),
        "file_exists": path.exists(),
        "content_hash": _sha256_file(path),
        "rule_family": _norm(payload.get("rule_family")),
        "group_counts": group_counts,
        "entry_count": len(entries),
    }


def _build_backup_file(output_dir: Path) -> str:
    backup_dir = output_dir / "rollback_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / "formal_scope_rules.before_324l.json"
    if FORMAL_SCOPE_RULES_PATH.exists():
        backup_path.write_text(FORMAL_SCOPE_RULES_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        backup_path.write_text(
            json.dumps({"file_exists": False, "path": str(FORMAL_SCOPE_RULES_PATH)}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return str(backup_path)


def load_official_patch_application_324l_inputs(
    reviewed_dir: Path,
    dry_run_dir: Path,
) -> Dict[str, Any]:
    return {
        "reviewed_summary": _read_json(
            reviewed_dir / "controlled_official_proposal_human_approval_324k_reviewed_summary.json"
        ),
        "reviewed_qa": _read_json(
            reviewed_dir / "controlled_official_proposal_human_approval_324k_reviewed_qa.json"
        ),
        "reviewed_result": _read_json(
            reviewed_dir / "controlled_official_proposal_human_approval_324k_reviewed_result.json"
        ),
        "dry_run_summary": _read_json(
            dry_run_dir / "controlled_official_proposal_dry_run_324j_summary.json"
        ),
        "dry_run_qa": _read_json(
            dry_run_dir / "controlled_official_proposal_dry_run_324j_qa.json"
        ),
        "patch_operations_json": _read_json(
            dry_run_dir / "controlled_official_proposal_dry_run_324j_patch_operations.json"
        ),
        "target_diff_json": _read_json(
            dry_run_dir / "controlled_official_proposal_dry_run_324j_target_asset_diff_preview.json"
        ),
    }


def _validate_reviewed_readiness(summary: Dict[str, Any], qa: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        rows.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add("readiness::324k_reviewed_decision", _norm(summary.get("decision")) == EXPECTED_324K_REVIEWED_DECISION, _norm(summary.get("decision")))
    add("readiness::324k_reviewed_summary_qa_fail_count", _safe_int(summary.get("qa_fail_count")) == 0, str(summary.get("qa_fail_count", "")))
    add("readiness::324k_reviewed_qa_json_fail_count", _safe_int(qa.get("qa_fail_count")) == 0, str(qa.get("qa_fail_count", "")))
    expected_pairs = [
        ("approval_record_count", 1),
        ("approved_count", 1),
        ("rejected_count", 0),
        ("needs_more_info_count", 0),
        ("pending_count", 0),
        ("invalid_decision_count", 0),
    ]
    for key, expected in expected_pairs:
        add(f"readiness::324k_reviewed_{key}", _safe_int(summary.get(key)) == expected, f"expected={expected} actual={summary.get(key, '')}")
    return rows


def _validate_dry_run_readiness(summary: Dict[str, Any], qa: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        rows.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add("readiness::324j_decision", _norm(summary.get("decision")) == EXPECTED_324J_DECISION, _norm(summary.get("decision")))
    add("readiness::324j_summary_qa_fail_count", _safe_int(summary.get("qa_fail_count")) == 0, str(summary.get("qa_fail_count", "")))
    add("readiness::324j_qa_json_fail_count", _safe_int(qa.get("qa_fail_count")) == 0, str(qa.get("qa_fail_count", "")))
    for key, expected in [
        ("proposal_count", 1),
        ("patch_operation_count", 1),
        ("scope_patch_operation_count", 1),
        ("alias_patch_operation_count", 0),
        ("duplicate_operation_count", 0),
        ("target_conflict_count", 0),
        ("already_official_overlap_count", 0),
        ("expected_affected_candidate_count", 42),
        ("expected_trusted_gain", 0),
        ("expected_review_reduction", 42),
        ("expected_out_of_scope_or_rejected_gain", 42),
    ]:
        add(f"readiness::324j_{key}", _safe_int(summary.get(key)) == expected, f"expected={expected} actual={summary.get(key, '')}")
    return rows


def _build_approved_operations(reviewed_result: Dict[str, Any]) -> Tuple[List[ApprovedOperation], List[Dict[str, Any]]]:
    rows: List[Dict[str, Any]] = []
    checks: List[Dict[str, Any]] = []
    approved_rows = reviewed_result.get("approved_records", [])
    approved_rows = approved_rows if isinstance(approved_rows, list) else []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add("approved_records::count", len(approved_rows) == 1, f"actual={len(approved_rows)}")
    for row in approved_rows:
        if not isinstance(row, dict):
            continue
        proposed_change = _parse_json(row.get("proposed_change"))
        generated_rule_id = _generated_rule_id(row.get("approval_id"))
        rows.append(
            ApprovedOperation(
                approval_id=_norm(row.get("approval_id")),
                reviewer_decision=_norm(row.get("reviewer_decision")),
                reviewer_name=_norm(row.get("reviewer_name")),
                reviewer_note=_norm(row.get("reviewer_note")),
                approval_timestamp=_norm(row.get("approval_timestamp")),
                dry_run_patch_operation_id=_norm(row.get("dry_run_patch_operation_id")),
                controlled_proposal_id_324i=_norm(row.get("controlled_proposal_id_324i")),
                source_rule_candidate_id_324h=_norm(row.get("source_rule_candidate_id_324h")),
                candidate_type=_norm(row.get("candidate_type")),
                patch_operation_type=_norm(row.get("patch_operation_type")),
                proposal_type=_norm(row.get("proposal_type")),
                target_asset_path=_norm(row.get("target_asset_path")),
                target_group_name=_norm(row.get("target_group_name")),
                target_locator=_norm(row.get("target_locator")),
                normalized_label=_norm(row.get("normalized_label")),
                proposed_change=proposed_change,
                expected_affected_candidate_count=_safe_int(row.get("expected_affected_candidate_count")),
                expected_trusted_gain=_safe_int(row.get("expected_trusted_gain")),
                expected_review_reduction=_safe_int(row.get("expected_review_reduction")),
                expected_out_of_scope_or_rejected_gain=_safe_int(row.get("expected_out_of_scope_or_rejected_gain")),
                source_candidate_ids_324a=_norm(row.get("source_candidate_ids_324a")),
                source_review_ids_324b=_norm(row.get("source_review_ids_324b")),
                source_request_ids_324c=_norm(row.get("source_request_ids_324c")),
                source_response_ids_324d=_norm(row.get("source_response_ids_324d")),
                source_validation_ids_324e=_norm(row.get("source_validation_ids_324e")),
                source_confirmation_ids_324f=_norm(row.get("source_confirmation_ids_324f")),
                source_sandbox_rule_ids_324g=_norm(row.get("source_sandbox_rule_ids_324g")),
                provenance=_norm(row.get("provenance")),
                dry_run_evidence=_norm(row.get("dry_run_evidence")),
                rollback_note=_norm(row.get("rollback_note")),
                warning_notes=_norm(row.get("warning_notes")),
                risk_flags=_norm(row.get("risk_flags")),
                generated_rule_id=generated_rule_id,
                scope_action=_norm(proposed_change.get("scope_action")) or SCOPE_ACTION,
            )
        )

    duplicate_approval_ids = len({row.approval_id for row in rows}) != len(rows)
    duplicate_patch_ids = len({row.dry_run_patch_operation_id for row in rows}) != len(rows)
    add("approved_records::no_duplicate_approval_ids", not duplicate_approval_ids, f"duplicate_present={duplicate_approval_ids}")
    add("approved_records::no_duplicate_patch_operation_ids", not duplicate_patch_ids, f"duplicate_present={duplicate_patch_ids}")

    required_failures = 0
    for row in rows:
        if not all(
            [
                row.approval_id,
                row.dry_run_patch_operation_id,
                row.controlled_proposal_id_324i,
                row.source_rule_candidate_id_324h,
                row.reviewer_decision == "APPROVE",
                row.patch_operation_type == "ADD_SCOPE_EXCLUSION",
                row.target_asset_path == str(FORMAL_SCOPE_RULES_PATH),
                row.target_group_name == SCOPE_TARGET_GROUP,
                row.normalized_label,
            ]
        ):
            required_failures += 1
    add("approved_records::required_fields_complete", required_failures == 0, f"failed_records={required_failures}")
    return rows, checks


def _build_rule(operation: ApprovedOperation) -> Dict[str, Any]:
    return {
        "rule_id": operation.generated_rule_id,
        "rule_type": "core_metric_scope_exclusion",
        "target_group": operation.target_group_name,
        "normalized_label": operation.normalized_label,
        "scope_action": operation.scope_action,
        "existing_scope": operation.scope_action,
        "scope_applicability": [
            "GLOBAL_ALIAS_MATCH_ONLY",
            "EXCLUDE_FROM_CORE_METRIC_MAPPING",
        ],
        "source_approval_id": operation.approval_id,
        "source_dry_run_patch_operation_id": operation.dry_run_patch_operation_id,
        "source_controlled_proposal_id": operation.controlled_proposal_id_324i,
        "source_rule_candidate_id_324h": operation.source_rule_candidate_id_324h,
        "source_candidate_ids_324a": operation.source_candidate_ids_324a,
        "source_review_ids_324b": operation.source_review_ids_324b,
        "source_request_ids_324c": operation.source_request_ids_324c,
        "source_response_ids_324d": operation.source_response_ids_324d,
        "source_validation_ids_324e": operation.source_validation_ids_324e,
        "source_confirmation_ids_324f": operation.source_confirmation_ids_324f,
        "source_sandbox_rule_ids_324g": operation.source_sandbox_rule_ids_324g,
        "reviewer_name": operation.reviewer_name,
        "reviewer_note": operation.reviewer_note,
        "approval_timestamp": operation.approval_timestamp,
        "warning_notes": operation.warning_notes,
        "risk_flags": operation.risk_flags,
        "promotion_status": "PROMOTED_324L_OFFICIAL_PATCH",
    }


def _prepare_precheck(
    operations: Sequence[ApprovedOperation],
    scope_payload: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], int]:
    scope_entries = _flatten_scope_entries(scope_payload)
    rows: List[Dict[str, Any]] = []
    conflict_count = 0
    for operation in operations:
        matches = [
            row
            for row in scope_entries
            if _norm(row.get("target_group")) == operation.target_group_name
            and _normalize_label(row.get("normalized_label")) == _normalize_label(operation.normalized_label)
        ]
        exact_match = next(
            (
                row
                for row in matches
                if _norm(row.get("scope_action")) == operation.scope_action
            ),
            None,
        )
        conflicting_match = next(
            (
                row
                for row in matches
                if _norm(row.get("scope_action")) != operation.scope_action
            ),
            None,
        )
        generated_rule_conflict = next(
            (
                row
                for row in scope_entries
                if _norm(row.get("rule_id")) == operation.generated_rule_id
                and (
                    _normalize_label(row.get("normalized_label")) != _normalize_label(operation.normalized_label)
                    or _norm(row.get("scope_action")) != operation.scope_action
                )
            ),
            None,
        )
        group_before_count = int(
            sum(1 for row in scope_entries if _norm(row.get("target_group")) == operation.target_group_name)
        )
        if exact_match:
            status = "IDEMPOTENT_ALREADY_APPLIED"
            before_state = exact_match
        elif conflicting_match or generated_rule_conflict:
            status = "CONFLICT"
            before_state = conflicting_match or generated_rule_conflict
            conflict_count += 1
        elif operation.target_asset_path != str(FORMAL_SCOPE_RULES_PATH) or operation.target_group_name != SCOPE_TARGET_GROUP:
            status = "CONFLICT"
            before_state = {}
            conflict_count += 1
        else:
            status = "READY_TO_APPLY"
            before_state = {}

        rows.append(
            {
                "approval_id": operation.approval_id,
                "dry_run_patch_operation_id": operation.dry_run_patch_operation_id,
                "candidate_type": operation.candidate_type,
                "patch_operation_type": operation.patch_operation_type,
                "target_asset_path": operation.target_asset_path,
                "target_group_name": operation.target_group_name,
                "generated_rule_id": operation.generated_rule_id,
                "normalized_label": operation.normalized_label,
                "group_before_entry_count": group_before_count,
                "group_after_entry_count_preview": group_before_count + (0 if status == "IDEMPOTENT_ALREADY_APPLIED" else 1),
                "precheck_status": status,
                "before_state": before_state,
            }
        )
    return rows, conflict_count


def _apply_operations(
    operations: Sequence[ApprovedOperation],
    precheck_rows: Sequence[Dict[str, Any]],
    scope_payload: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    mutable_payload = deepcopy(scope_payload)
    rules = mutable_payload.setdefault("rules", {})
    if not isinstance(rules, dict):
        rules = {}
        mutable_payload["rules"] = rules

    precheck_lookup = {_norm(row.get("approval_id")): row for row in precheck_rows}
    logs: List[Dict[str, Any]] = []
    for operation in operations:
        precheck = precheck_lookup.get(operation.approval_id, {})
        status = _norm(precheck.get("precheck_status"))
        before_state = precheck.get("before_state") or {}
        after_state: Dict[str, Any] | None = None
        if status == "READY_TO_APPLY":
            new_rule = _build_rule(operation)
            rules[operation.generated_rule_id] = new_rule
            after_state = new_rule
            status = "APPLIED"
        elif status == "IDEMPOTENT_ALREADY_APPLIED":
            after_state = before_state

        logs.append(
            {
                "approval_id": operation.approval_id,
                "dry_run_patch_operation_id": operation.dry_run_patch_operation_id,
                "controlled_proposal_id_324i": operation.controlled_proposal_id_324i,
                "candidate_type": operation.candidate_type,
                "patch_operation_type": operation.patch_operation_type,
                "operation_status": status,
                "target_asset_path": operation.target_asset_path,
                "target_group_name": operation.target_group_name,
                "generated_rule_id": operation.generated_rule_id,
                "normalized_label": operation.normalized_label,
                "scope_action": operation.scope_action,
                "before_state": before_state,
                "after_state": after_state,
                "expected_affected_candidate_count": operation.expected_affected_candidate_count,
                "expected_trusted_gain": operation.expected_trusted_gain,
                "expected_review_reduction": operation.expected_review_reduction,
                "expected_out_of_scope_or_rejected_gain": operation.expected_out_of_scope_or_rejected_gain,
                "source_rule_candidate_id_324h": operation.source_rule_candidate_id_324h,
                "source_candidate_ids_324a": operation.source_candidate_ids_324a,
                "source_review_ids_324b": operation.source_review_ids_324b,
                "source_request_ids_324c": operation.source_request_ids_324c,
                "source_response_ids_324d": operation.source_response_ids_324d,
                "source_validation_ids_324e": operation.source_validation_ids_324e,
                "source_confirmation_ids_324f": operation.source_confirmation_ids_324f,
                "source_sandbox_rule_ids_324g": operation.source_sandbox_rule_ids_324g,
                "rollback_note": operation.rollback_note,
                "warning_notes": operation.warning_notes,
                "risk_flags": operation.risk_flags,
            }
        )
    return mutable_payload, logs


def _build_rollback_rows(logs: Sequence[Dict[str, Any]], backup_path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for log_row in logs:
        status = _norm(log_row.get("operation_status"))
        rows.append(
            {
                "approval_id": _norm(log_row.get("approval_id")),
                "dry_run_patch_operation_id": _norm(log_row.get("dry_run_patch_operation_id")),
                "candidate_type": _norm(log_row.get("candidate_type")),
                "generated_rule_id": _norm(log_row.get("generated_rule_id")),
                "target_path": str(FORMAL_SCOPE_RULES_PATH),
                "operation_status": status,
                "rollback_action": "restore_asset_from_backup" if status == "APPLIED" else "no_action_required_idempotent",
                "backup_path": backup_path,
                "rollback_note": _norm(log_row.get("rollback_note")),
            }
        )
    return rows


def _asset_diff_rows(before_snapshot: Dict[str, Any], after_snapshot: Dict[str, Any], logs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    before_by_path = {item["path"]: item for item in before_snapshot.get("assets", [])}
    after_by_path = {item["path"]: item for item in after_snapshot.get("assets", [])}
    rows: List[Dict[str, Any]] = []
    for path, before_item in before_by_path.items():
        after_item = after_by_path.get(path, {})
        rows.append(
            {
                "target_path": path,
                "before_hash": before_item.get("content_hash", ""),
                "after_hash": after_item.get("content_hash", ""),
                "before_entry_count": before_item.get("entry_count", 0),
                "after_entry_count": after_item.get("entry_count", 0),
                "changed": before_item.get("content_hash") != after_item.get("content_hash"),
                "rule_family": after_item.get("rule_family") or before_item.get("rule_family"),
            }
        )
    for log_row in logs:
        rows.append(
            {
                "target_path": str(FORMAL_SCOPE_RULES_PATH),
                "operation_status": _norm(log_row.get("operation_status")),
                "candidate_type": _norm(log_row.get("candidate_type")),
                "target_group_name": _norm(log_row.get("target_group_name")),
                "generated_rule_id": _norm(log_row.get("generated_rule_id")),
                "approval_id": _norm(log_row.get("approval_id")),
                "before_state": json.dumps(_to_jsonable(log_row.get("before_state")), ensure_ascii=False),
                "after_state": json.dumps(_to_jsonable(log_row.get("after_state")), ensure_ascii=False),
                "rollback_note": _norm(log_row.get("rollback_note")),
            }
        )
    return rows


def build_official_patch_application_324l(
    reviewed_summary: Dict[str, Any],
    reviewed_qa: Dict[str, Any],
    reviewed_result: Dict[str, Any],
    dry_run_summary: Dict[str, Any],
    dry_run_qa: Dict[str, Any],
    patch_operations_json: Dict[str, Any],
    output_dir: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    qa_rows.extend(_validate_reviewed_readiness(reviewed_summary, reviewed_qa))
    qa_rows.extend(_validate_dry_run_readiness(dry_run_summary, dry_run_qa))

    operations, approved_checks = _build_approved_operations(reviewed_result)
    qa_rows.extend(approved_checks)

    patch_rows = patch_operations_json.get("patch_operations", [])
    patch_rows = patch_rows if isinstance(patch_rows, list) else []
    patch_lookup = {
        _norm(row.get("dry_run_patch_operation_id")): row
        for row in patch_rows
        if isinstance(row, dict)
    }
    add_qa("dry_run_patch_operations::count", len(patch_rows) == 1, f"actual={len(patch_rows)}")
    for operation in operations:
        patch_row = patch_lookup.get(operation.dry_run_patch_operation_id, {})
        add_qa(
            f"patch_alignment::{operation.approval_id}::exists",
            bool(patch_row),
            operation.dry_run_patch_operation_id,
        )
        add_qa(
            f"patch_alignment::{operation.approval_id}::operation_type",
            _norm(patch_row.get("patch_operation_type")) == "ADD_SCOPE_EXCLUSION",
            _norm(patch_row.get("patch_operation_type")),
        )
        add_qa(
            f"patch_alignment::{operation.approval_id}::target_asset",
            _norm(patch_row.get("target_asset_path")) == str(FORMAL_SCOPE_RULES_PATH),
            _norm(patch_row.get("target_asset_path")),
        )
        add_qa(
            f"patch_alignment::{operation.approval_id}::target_group",
            _norm(patch_row.get("target_group_name")) == SCOPE_TARGET_GROUP,
            _norm(patch_row.get("target_group_name")),
        )

    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    alias_hash_before = _sha256_file(SEMANTIC_ALIAS_ASSET_PATH)
    before_snapshot = {
        "stage": "324L",
        "snapshot_type": "before",
        "assets": [
            _snapshot_asset(FORMAL_SCOPE_RULES_PATH, "scope"),
            _snapshot_asset(SEMANTIC_ALIAS_ASSET_PATH, "alias"),
        ],
    }
    add_qa("before_snapshot::generated", "PASS", f"asset_count={len(before_snapshot['assets'])}")

    backup_path = _build_backup_file(output_dir)
    add_qa(
        "rollback::formal_scope_rules_backup_created",
        "PASS" if Path(backup_path).exists() else "FAIL",
        backup_path,
    )

    scope_payload = _load_scope_asset()
    add_qa(
        "target_assets::formal_scope_rules_readable",
        "PASS" if isinstance(scope_payload.get("rules"), dict) else "FAIL",
        str(FORMAL_SCOPE_RULES_PATH),
    )
    add_qa(
        "target_assets::alias_asset_readable",
        "PASS" if SEMANTIC_ALIAS_ASSET_PATH.exists() else "FAIL",
        str(SEMANTIC_ALIAS_ASSET_PATH),
    )

    precheck_rows, conflict_count = _prepare_precheck(operations, scope_payload)
    for row in precheck_rows:
        status = _norm(row.get("precheck_status"))
        add_qa(
            f"preapply::{_norm(row.get('approval_id'))}",
            "PASS" if status in {"READY_TO_APPLY", "IDEMPOTENT_ALREADY_APPLIED"} else "FAIL",
            f"status={status} label={_norm(row.get('normalized_label'))}",
        )
    add_qa("preapply::conflict_count", "PASS" if conflict_count == 0 else "FAIL", f"actual={conflict_count}")

    apply_blocked = any(row["status"] == "FAIL" for row in qa_rows) or conflict_count > 0
    logs: List[Dict[str, Any]] = []
    if not apply_blocked:
        scope_after_payload, logs = _apply_operations(
            operations=operations,
            precheck_rows=precheck_rows,
            scope_payload=scope_payload,
        )
        if any(_norm(row.get("operation_status")) == "APPLIED" for row in logs):
            _write_scope_asset(scope_after_payload)

    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    alias_hash_after = _sha256_file(SEMANTIC_ALIAS_ASSET_PATH)
    after_snapshot = {
        "stage": "324L",
        "snapshot_type": "after",
        "assets": [
            _snapshot_asset(FORMAL_SCOPE_RULES_PATH, "scope"),
            _snapshot_asset(SEMANTIC_ALIAS_ASSET_PATH, "alias"),
        ],
    }
    add_qa("after_snapshot::generated", "PASS", f"asset_count={len(after_snapshot['assets'])}")

    applied_count = int(sum(1 for row in logs if _norm(row.get("operation_status")) == "APPLIED"))
    idempotent_count = int(sum(1 for row in logs if _norm(row.get("operation_status")) == "IDEMPOTENT_ALREADY_APPLIED"))
    applied_or_idempotent_count = applied_count + idempotent_count

    add_qa(
        "application::approved_patch_operation_count",
        "PASS" if len(operations) == 1 else "FAIL",
        f"actual={len(operations)}",
    )
    add_qa("application::scope_approved_patch_operation_count", "PASS" if len(operations) == 1 else "FAIL", f"actual={len(operations)}")
    add_qa("application::alias_approved_patch_operation_count", "PASS", "actual=0")
    add_qa(
        "application::applied_or_idempotent_operation_count",
        "PASS" if applied_or_idempotent_count == 1 else "FAIL",
        f"applied={applied_count} idempotent={idempotent_count}",
    )
    add_qa(
        "safety::alias_asset_unchanged",
        "PASS" if alias_hash_before == alias_hash_after else "FAIL",
        f"before={alias_hash_before} after={alias_hash_after}",
    )
    add_qa(
        "safety::only_scope_asset_written",
        "PASS"
        if (
            (applied_count == 0 and scope_hash_before == scope_hash_after)
            or (applied_count == 1 and scope_hash_before != scope_hash_after)
        )
        else "FAIL",
        f"scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )

    duplicate_count_before = _count_scope_duplicates(scope_payload)
    duplicate_count_after = _count_scope_duplicates(_load_scope_asset())
    duplicate_count_delta = duplicate_count_after - duplicate_count_before
    add_qa(
        "postapply::no_new_scope_duplicates",
        "PASS" if duplicate_count_delta == 0 else "FAIL",
        f"before={duplicate_count_before} after={duplicate_count_after} delta={duplicate_count_delta}",
    )

    rerun_precheck_rows, rerun_conflict_count = _prepare_precheck(operations, _load_scope_asset())
    rerun_all_idempotent = all(
        _norm(row.get("precheck_status")) == "IDEMPOTENT_ALREADY_APPLIED"
        for row in rerun_precheck_rows
    ) if rerun_precheck_rows else False
    add_qa(
        "idempotency::rerun_would_be_idempotent",
        "PASS" if rerun_all_idempotent and rerun_conflict_count == 0 else "FAIL",
        f"rows={len(rerun_precheck_rows)} conflicts={rerun_conflict_count}",
    )

    rule_visible = any(
        _norm(row.get("rule_id")) == operations[0].generated_rule_id
        for row in _flatten_scope_entries(_load_scope_asset())
    ) if operations else False
    add_qa("postapply::generated_rule_visible", "PASS" if rule_visible else "FAIL", operations[0].generated_rule_id if operations else "")

    before_by_path = {item["path"]: item for item in before_snapshot["assets"]}
    after_by_path = {item["path"]: item for item in after_snapshot["assets"]}
    before_after_preview_rows = [
        {
            "target_asset_path": str(FORMAL_SCOPE_RULES_PATH),
            "target_group_name": SCOPE_TARGET_GROUP,
            "candidate_type": "scope_noise",
            "before_entry_count": before_by_path.get(str(FORMAL_SCOPE_RULES_PATH), {}).get("group_counts", {}).get(SCOPE_TARGET_GROUP, 0),
            "after_entry_count": after_by_path.get(str(FORMAL_SCOPE_RULES_PATH), {}).get("group_counts", {}).get(SCOPE_TARGET_GROUP, 0),
            "added_operation_count": applied_count,
            "affected_candidate_count": int(sum(row.expected_affected_candidate_count for row in operations)),
            "expected_trusted_gain": int(sum(row.expected_trusted_gain for row in operations)),
            "expected_review_reduction": int(sum(row.expected_review_reduction for row in operations)),
            "expected_out_of_scope_or_rejected_gain": int(sum(row.expected_out_of_scope_or_rejected_gain for row in operations)),
        },
        {
            "target_asset_path": str(SEMANTIC_ALIAS_ASSET_PATH),
            "target_group_name": "",
            "candidate_type": "alias_guard",
            "before_entry_count": before_by_path.get(str(SEMANTIC_ALIAS_ASSET_PATH), {}).get("entry_count", 0),
            "after_entry_count": after_by_path.get(str(SEMANTIC_ALIAS_ASSET_PATH), {}).get("entry_count", 0),
            "added_operation_count": 0,
            "affected_candidate_count": 0,
            "expected_trusted_gain": 0,
            "expected_review_reduction": 0,
            "expected_out_of_scope_or_rejected_gain": 0,
        },
    ]

    rollback_rows = _build_rollback_rows(logs, backup_path)
    asset_diff_rows = _asset_diff_rows(before_snapshot, after_snapshot, logs)

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = (
        qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist()
        if not qa_df.empty
        else []
    )

    summary = {
        "stage": "324L",
        "output_dir": str(output_dir),
        "approved_patch_operation_count": len(operations),
        "alias_approved_patch_operation_count": 0,
        "scope_approved_patch_operation_count": len(operations),
        "applied_operation_count": applied_count,
        "idempotent_operation_count": idempotent_count,
        "applied_or_idempotent_operation_count": applied_or_idempotent_count,
        "target_official_assets_modified": (
            [str(FORMAL_SCOPE_RULES_PATH)] if scope_hash_before != scope_hash_after else []
        ),
        "alias_official_asset_unchanged_confirmed": alias_hash_before == alias_hash_after,
        "affected_candidate_count": int(sum(row.expected_affected_candidate_count for row in operations)),
        "expected_affected_candidate_count": int(sum(row.expected_affected_candidate_count for row in operations)),
        "expected_trusted_gain": int(sum(row.expected_trusted_gain for row in operations)),
        "expected_review_reduction": int(sum(row.expected_review_reduction for row in operations)),
        "expected_out_of_scope_or_rejected_gain": int(sum(row.expected_out_of_scope_or_rejected_gain for row in operations)),
        "duplicate_count_before": duplicate_count_before,
        "duplicate_count_after": duplicate_count_after,
        "duplicate_count_delta": duplicate_count_delta,
        "conflict_count": conflict_count,
        "rollback_backup_paths": {
            "scope_backup_path": backup_path,
        },
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": EXPECTED_324L_DECISION if qa_fail_count == 0 else EXPECTED_324L_NOT_READY,
    }

    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }

    apply_proof_json = {
        "stage": "324L",
        "decision": summary["decision"],
        "files_read": [
            str(Path(r"D:\_datefac\output\controlled_official_proposal_human_approval_324k_reviewed\controlled_official_proposal_human_approval_324k_reviewed_summary.json")),
            str(Path(r"D:\_datefac\output\controlled_official_proposal_human_approval_324k_reviewed\controlled_official_proposal_human_approval_324k_reviewed_qa.json")),
            str(Path(r"D:\_datefac\output\controlled_official_proposal_human_approval_324k_reviewed\controlled_official_proposal_human_approval_324k_reviewed_result.json")),
            str(Path(r"D:\_datefac\output\controlled_official_proposal_dry_run_324j\controlled_official_proposal_dry_run_324j_summary.json")),
            str(Path(r"D:\_datefac\output\controlled_official_proposal_dry_run_324j\controlled_official_proposal_dry_run_324j_qa.json")),
            str(Path(r"D:\_datefac\output\controlled_official_proposal_dry_run_324j\controlled_official_proposal_dry_run_324j_patch_operations.json")),
            str(FORMAL_SCOPE_RULES_PATH),
            str(SEMANTIC_ALIAS_ASSET_PATH),
        ],
        "official_assets_before": {
            str(FORMAL_SCOPE_RULES_PATH): scope_hash_before,
            str(SEMANTIC_ALIAS_ASSET_PATH): alias_hash_before,
        },
        "official_assets_after": {
            str(FORMAL_SCOPE_RULES_PATH): scope_hash_after,
            str(SEMANTIC_ALIAS_ASSET_PATH): alias_hash_after,
        },
        "official_assets_written": summary["target_official_assets_modified"],
        "approved_patch_operation_ids": [row.dry_run_patch_operation_id for row in operations],
        "applied_patch_operation_ids": [
            _norm(row.get("dry_run_patch_operation_id"))
            for row in logs
            if _norm(row.get("operation_status")) == "APPLIED"
        ],
        "idempotent_patch_operation_ids": [
            _norm(row.get("dry_run_patch_operation_id"))
            for row in logs
            if _norm(row.get("operation_status")) == "IDEMPOTENT_ALREADY_APPLIED"
        ],
        "alias_asset_unchanged": alias_hash_before == alias_hash_after,
        "rollback_backups": summary["rollback_backup_paths"],
    }

    before_snapshot_df = pd.DataFrame(before_snapshot["assets"]).fillna("")
    after_snapshot_df = pd.DataFrame(after_snapshot["assets"]).fillna("")
    before_after_preview_df = pd.DataFrame(before_after_preview_rows).fillna("")
    asset_diff_df = pd.DataFrame(asset_diff_rows).fillna("")
    application_log_df = pd.DataFrame(logs).fillna("")
    rollback_plan_df = pd.DataFrame(rollback_rows).fillna("")
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
                "limitation": "single_scope_only",
                "detail": "324L applies only the single approved 324K scope patch operation.",
            },
            {
                "limitation": "alias_asset_guard",
                "detail": "324L reads the official alias asset only for before/after safety hashing and never writes it.",
            },
        ]
    ).fillna("")

    return {
        "summary": summary,
        "before_snapshot_json": before_snapshot,
        "after_snapshot_json": after_snapshot,
        "qa_json": qa_json,
        "apply_proof_json": apply_proof_json,
        "application_log_rows": logs,
        "rollback_plan_rows": rollback_rows,
        "before_snapshot_df": before_snapshot_df,
        "after_snapshot_df": after_snapshot_df,
        "before_after_preview_df": before_after_preview_df,
        "asset_diff_df": asset_diff_df,
        "application_log_df": application_log_df,
        "rollback_plan_df": rollback_plan_df,
        "qa_summary_df": qa_summary_df,
        "qa_checks_df": qa_df,
        "known_limitations_df": known_limitations_df,
    }
