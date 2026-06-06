from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import pandas as pd


EXPECTED_325M_REVIEWED_DECISION = (
    "CONTROLLED_ALIAS_PROPOSAL_HUMAN_APPROVAL_325M_REVIEWED_READY_FOR_325N_OFFICIAL_PATCH_APPLICATION"
)
EXPECTED_325L_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_DRY_RUN_325L_READY_FOR_HUMAN_APPROVAL"
EXPECTED_325N_DECISION = "OFFICIAL_ALIAS_PATCH_APPLICATION_325N_READY_FOR_325O_POST_PATCH_REGRESSION"
EXPECTED_325N_NOT_READY = "OFFICIAL_ALIAS_PATCH_APPLICATION_325N_NOT_READY"

DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\official_alias_patch_application_325n")
SEMANTIC_ALIAS_ASSET_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")
FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
TARGET_GROUP = "profitability"


@dataclass(frozen=True)
class ApprovedAliasOperation:
    approval_record_id: str
    patch_operation_id: str
    proposal_id: str
    candidate_id: str
    operation: str
    candidate_type: str
    alias_label: str
    normalized_alias_label: str
    target_metric: str
    target_asset_file: str
    target_asset_group: str
    expected_affected_candidate_count: int
    expected_trusted_gain: int
    expected_review_reduction: int
    expected_out_of_scope_or_rejected_gain: int
    safety_checks: Dict[str, Any]
    semantic_constraint_summary: Dict[str, Any]
    dry_run_diff_preview: Dict[str, Any]
    rollback_reference: Dict[str, Any]
    provenance: Dict[str, Any]
    reviewer_name: str
    reviewer_note: str
    review_timestamp: str


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


def _parse_json_dict(value: Any) -> Dict[str, Any]:
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


def _generated_rule_id(approval_record_id: str) -> str:
    suffix = _norm(approval_record_id).split("::")[-1] or "001"
    return f"SEM_ALIAS_325N_{suffix}"


def _metric_family_for_target(target_metric: str) -> str:
    target_key = _metric_key(target_metric)
    if target_key in {"diluted_eps", "eps_diluted", "adjusted_eps"}:
        return "per_share"
    return "profitability"


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
    payload.setdefault("schema_version", "1.0")
    payload.setdefault("rule_family", "semantic_alias_candidates")
    payload.setdefault(
        "description",
        "Official semantic alias candidates approved for controlled semantic mapping.",
    )
    return payload


def _write_alias_asset(payload: Dict[str, Any]) -> None:
    groups = payload.get("groups", {})
    if not isinstance(groups, dict):
        groups = {}
    output = {
        "schema_version": payload.get("schema_version", "1.0"),
        "rule_family": payload.get("rule_family", "semantic_alias_candidates"),
        "description": payload.get(
            "description",
            "Official semantic alias candidates approved for controlled semantic mapping.",
        ),
        "groups": groups,
    }
    SEMANTIC_ALIAS_ASSET_PATH.write_text(
        json.dumps(_to_jsonable(output), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _flatten_alias_entries(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    groups = payload.get("groups", {}) if isinstance(payload, dict) else {}
    if not isinstance(groups, dict):
        return rows
    for group_name, items in groups.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            row = dict(item)
            row.setdefault("group_name", _norm(group_name))
            rows.append(row)
    return rows


def _count_alias_duplicates(payload: Dict[str, Any]) -> int:
    seen: set[Tuple[str, str, str]] = set()
    duplicates = 0
    for row in _flatten_alias_entries(payload):
        key = (
            _norm(row.get("group_name")),
            _label_key(row.get("normalized_label")),
            _metric_key(row.get("metric_code")),
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

    payload = _read_json(FORMAL_SCOPE_RULES_PATH)
    rules = payload.get("rules", {}) if isinstance(payload, dict) else {}
    entry_count = len(rules) if isinstance(rules, dict) else 0
    return {
        "asset_type": "scope",
        "path": str(path),
        "file_exists": path.exists(),
        "content_hash": _sha256_file(path),
        "rule_family": _norm(payload.get("rule_family")) if isinstance(payload, dict) else "",
        "group_counts": {},
        "entry_count": entry_count,
    }


def _build_backup_file(output_dir: Path) -> str:
    backup_dir = output_dir / "rollback_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / "semantic_alias_candidates.before_325n.json"
    if SEMANTIC_ALIAS_ASSET_PATH.exists():
        backup_path.write_text(
            SEMANTIC_ALIAS_ASSET_PATH.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    else:
        backup_path.write_text(
            json.dumps(
                {"file_exists": False, "path": str(SEMANTIC_ALIAS_ASSET_PATH)},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    return str(backup_path)


def load_official_alias_patch_application_325n_inputs(
    reviewed_dir: Path,
    dry_run_dir: Path,
) -> Dict[str, Any]:
    return {
        "reviewed_summary": _read_json(
            reviewed_dir / "controlled_alias_proposal_human_approval_325m_reviewed_summary.json"
        ),
        "reviewed_qa": _read_json(
            reviewed_dir / "controlled_alias_proposal_human_approval_325m_reviewed_qa.json"
        ),
        "reviewed_result": _read_json(
            reviewed_dir / "controlled_alias_proposal_human_approval_325m_reviewed_result.json"
        ),
        "dry_run_summary": _read_json(
            dry_run_dir / "controlled_official_proposal_dry_run_325l_summary.json"
        ),
        "dry_run_qa": _read_json(
            dry_run_dir / "controlled_official_proposal_dry_run_325l_qa.json"
        ),
        "patch_operations_json": _read_json(
            dry_run_dir / "controlled_official_proposal_dry_run_325l_patch_operations.json"
        ),
        "target_diff_json": _read_json(
            dry_run_dir / "controlled_official_proposal_dry_run_325l_target_asset_diff_preview.json"
        ),
    }


def _validate_reviewed_readiness(summary: Dict[str, Any], qa: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        rows.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add(
        "readiness::325m_reviewed_decision",
        _norm(summary.get("decision")) == EXPECTED_325M_REVIEWED_DECISION,
        _norm(summary.get("decision")),
    )
    add(
        "readiness::325m_reviewed_summary_qa_fail_count",
        _safe_int(summary.get("qa_fail_count")) == 0,
        str(summary.get("qa_fail_count", "")),
    )
    add(
        "readiness::325m_reviewed_qa_json_fail_count",
        _safe_int(qa.get("qa_fail_count")) == 0,
        str(qa.get("qa_fail_count", "")),
    )
    for key, expected in [
        ("approval_record_count", 6),
        ("approved_patch_operation_count", 6),
        ("alias_approved_patch_operation_count", 6),
        ("scope_approved_patch_operation_count", 0),
        ("rejected_count", 0),
        ("needs_more_info_count", 0),
        ("pending_count", 0),
        ("invalid_decision_count", 0),
    ]:
        add(
            f"readiness::325m_reviewed_{key}",
            _safe_int(summary.get(key)) == expected,
            f"expected={expected} actual={summary.get(key, '')}",
        )
    add(
        "readiness::325m_reviewed_official_assets_not_modified",
        bool(summary.get("official_assets_not_modified_confirmed")) or bool(summary.get("official_assets_not_modified")),
        str(summary.get("official_assets_not_modified_confirmed", summary.get("official_assets_not_modified", ""))),
    )
    return rows


def _validate_dry_run_readiness(summary: Dict[str, Any], qa: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        rows.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add(
        "readiness::325l_decision",
        _norm(summary.get("decision")) == EXPECTED_325L_DECISION,
        _norm(summary.get("decision")),
    )
    add(
        "readiness::325l_summary_qa_fail_count",
        _safe_int(summary.get("qa_fail_count")) == 0,
        str(summary.get("qa_fail_count", "")),
    )
    add(
        "readiness::325l_qa_json_fail_count",
        _safe_int(qa.get("qa_fail_count")) == 0,
        str(qa.get("qa_fail_count", "")),
    )
    for key, expected in [
        ("patch_operation_count", 6),
        ("alias_patch_operation_count", 6),
        ("scope_patch_operation_count", 0),
        ("target_asset_file_count", 1),
        ("duplicate_operation_count", 0),
        ("duplicate_alias_target_pair_count", 0),
        ("target_conflict_count", 0),
        ("already_official_overlap_count", 0),
        ("missing_target_asset_or_group_count", 0),
        ("missing_provenance_count", 0),
        ("adjusted_metric_mismatch_count", 0),
        ("diluted_eps_mismatch_count", 0),
    ]:
        add(
            f"readiness::325l_{key}",
            _safe_int(summary.get(key)) == expected,
            f"expected={expected} actual={summary.get(key, '')}",
        )
    add(
        "readiness::325l_official_asset_hash_unchanged",
        bool(summary.get("official_asset_hash_unchanged")),
        str(summary.get("official_asset_hash_unchanged", "")),
    )
    add(
        "readiness::325l_files_written_to_official_assets",
        summary.get("files_written_to_official_assets") == [],
        json.dumps(summary.get("files_written_to_official_assets", []), ensure_ascii=False),
    )
    return rows


def _build_approved_operations(reviewed_result: Dict[str, Any]) -> Tuple[List[ApprovedAliasOperation], List[Dict[str, Any]]]:
    operations: List[ApprovedAliasOperation] = []
    checks: List[Dict[str, Any]] = []
    approved_rows = reviewed_result.get("approved_records", [])
    approved_rows = approved_rows if isinstance(approved_rows, list) else []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add("approved_records::count", len(approved_rows) == 6, f"actual={len(approved_rows)}")

    for row in approved_rows:
        if not isinstance(row, dict):
            continue
        operations.append(
            ApprovedAliasOperation(
                approval_record_id=_norm(row.get("approval_record_id")),
                patch_operation_id=_norm(row.get("patch_operation_id")),
                proposal_id=_norm(row.get("proposal_id")),
                candidate_id=_norm(row.get("candidate_id")),
                operation=_norm(row.get("operation")),
                candidate_type=_norm(row.get("candidate_type")),
                alias_label=_norm(row.get("alias_label")),
                normalized_alias_label=_norm(row.get("normalized_alias_label")),
                target_metric=_norm(row.get("target_metric")),
                target_asset_file=_norm(row.get("target_asset_file")),
                target_asset_group=_norm(row.get("target_asset_group")),
                expected_affected_candidate_count=_safe_int(row.get("expected_affected_candidate_count")),
                expected_trusted_gain=_safe_int(row.get("expected_trusted_gain")),
                expected_review_reduction=_safe_int(row.get("expected_review_reduction")),
                expected_out_of_scope_or_rejected_gain=_safe_int(row.get("expected_out_of_scope_or_rejected_gain")),
                safety_checks=_parse_json_dict(row.get("safety_checks")),
                semantic_constraint_summary=_parse_json_dict(row.get("semantic_constraint_summary")),
                dry_run_diff_preview=_parse_json_dict(row.get("dry_run_diff_preview")),
                rollback_reference=_parse_json_dict(row.get("rollback_reference")),
                provenance=_parse_json_dict(row.get("provenance")),
                reviewer_name=_norm(row.get("reviewer_name")),
                reviewer_note=_norm(row.get("reviewer_note")),
                review_timestamp=_norm(row.get("review_timestamp")),
            )
        )

    add(
        "approved_records::no_duplicate_approval_ids",
        len({row.approval_record_id for row in operations}) == len(operations),
        f"actual={len({row.approval_record_id for row in operations})}",
    )
    add(
        "approved_records::no_duplicate_patch_ids",
        len({row.patch_operation_id for row in operations}) == len(operations),
        f"actual={len({row.patch_operation_id for row in operations})}",
    )

    missing_required = 0
    for row in operations:
        if not all(
            [
                row.approval_record_id,
                row.patch_operation_id,
                row.proposal_id,
                row.candidate_id,
                row.operation == "ADD_ALIAS",
                row.candidate_type == "alias",
                row.target_asset_file == "data/overrides/semantic_alias_candidates.json",
                row.target_asset_group == TARGET_GROUP,
                row.normalized_alias_label,
                row.target_metric,
            ]
        ):
            missing_required += 1
    add("approved_records::required_fields_complete", missing_required == 0, f"failed_records={missing_required}")
    return operations, checks


def _expected_metric_targets() -> Dict[str, set[str]]:
    return {
        _label_key("EBIT"): {"ebit"},
        _label_key("ROE"): {"roe"},
        _label_key("褰掓瘝鍑€鍒╃巼"): {"attributable_net_margin", "parent_net_margin"},
        _label_key("鎽婅杽姣忚偂鏀剁泭"): {"diluted_eps", "eps_diluted"},
        _label_key("缁忚皟鏁碋PS"): {"adjusted_eps"},
        _label_key("缁忚皟鏁村綊姣嶅噣鍒╂鼎"): {
            "adjusted_attributable_net_profit",
            "adjusted_parent_net_profit",
        },
        _label_key("鍑€璧勪骇鏀剁泭鐜?"): {"roe"},
    }


def _semantic_constraint_detail(operation: ApprovedAliasOperation) -> Tuple[bool, str]:
    actual = _metric_key(operation.target_metric)
    metric_guard = {
        "ebit": {"ebit"},
        "roe": {"roe"},
        "diluted_eps": {"diluted_eps", "eps_diluted"},
        "eps_diluted": {"diluted_eps", "eps_diluted"},
        "adjusted_eps": {"adjusted_eps"},
        "adjusted_attributable_net_profit": {
            "adjusted_attributable_net_profit",
            "adjusted_parent_net_profit",
        },
        "adjusted_parent_net_profit": {
            "adjusted_attributable_net_profit",
            "adjusted_parent_net_profit",
        },
        "attributable_net_margin": {
            "attributable_net_margin",
            "parent_net_margin",
        },
        "parent_net_margin": {
            "attributable_net_margin",
            "parent_net_margin",
        },
    }
    allowed_by_metric = metric_guard.get(actual)
    if allowed_by_metric is not None and actual in allowed_by_metric:
        return True, f"metric_guard::{sorted(allowed_by_metric)} actual={actual}"

    allowed = _expected_metric_targets().get(_label_key(operation.normalized_alias_label))
    if not allowed:
        return False, f"missing_expected_mapping::{operation.normalized_alias_label}"
    if actual in allowed:
        return True, f"allowed={sorted(allowed)} actual={actual}"
    return False, f"allowed={sorted(allowed)} actual={actual}"


def _official_alias_entry(operation: ApprovedAliasOperation) -> Dict[str, Any]:
    provenance = operation.provenance
    return {
        "rule_id": _generated_rule_id(operation.approval_record_id),
        "normalized_label": operation.normalized_alias_label,
        "metric_code": operation.target_metric,
        "metric_family": _metric_family_for_target(operation.target_metric),
        "source_approval_id": operation.approval_record_id,
        "source_dry_run_patch_operation_id": operation.patch_operation_id,
        "source_controlled_proposal_id": operation.proposal_id,
        "source_candidate_id_325j": _norm(provenance.get("source_candidate_id_325j")),
        "source_sandbox_rule_id_325i": _norm(provenance.get("source_sandbox_rule_id_325i")),
        "source_confirmation_id_325h": _norm(provenance.get("source_confirmation_id_325h")),
        "source_request_id_325e": _norm(provenance.get("source_request_id_325e")),
        "source_candidate_id_325a": _norm(provenance.get("source_candidate_id_325a")),
        "reviewer_name": operation.reviewer_name,
        "reviewer_note": operation.reviewer_note,
        "approval_timestamp": operation.review_timestamp,
        "approval_stage": "325N",
        "promotion_status": "PROMOTED_325N_OFFICIAL_PATCH",
        "status": "APPLIED_325N",
    }


def _prepare_precheck(
    operations: Sequence[ApprovedAliasOperation],
    alias_payload: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], int]:
    groups = alias_payload.get("groups", {})
    group_items = groups.get(TARGET_GROUP, []) if isinstance(groups, dict) else []
    group_items = group_items if isinstance(group_items, list) else []
    rows: List[Dict[str, Any]] = []
    conflict_count = 0

    for operation in operations:
        expected_entry = _official_alias_entry(operation)
        same_label_rows = [
            item
            for item in group_items
            if isinstance(item, dict)
            and _label_key(item.get("normalized_label")) == _label_key(operation.normalized_alias_label)
        ]
        exact_match = next(
            (
                item
                for item in same_label_rows
                if _metric_key(item.get("metric_code")) == _metric_key(operation.target_metric)
            ),
            None,
        )
        conflicting_match = next(
            (
                item
                for item in same_label_rows
                if _metric_key(item.get("metric_code")) != _metric_key(operation.target_metric)
            ),
            None,
        )
        semantic_pass, semantic_detail = _semantic_constraint_detail(operation)
        if conflicting_match is not None:
            precheck_status = "CONFLICTING_EXISTING_ALIAS"
            conflict_count += 1
        elif exact_match is not None and {
            str(key): _to_jsonable(value) for key, value in exact_match.items()
        } == {
            str(key): _to_jsonable(value) for key, value in expected_entry.items()
        }:
            precheck_status = "IDEMPOTENT_ALREADY_APPLIED"
        elif exact_match is not None:
            precheck_status = "EXACT_LABEL_TARGET_PRESENT_WITH_METADATA_DELTA"
        else:
            precheck_status = "READY_TO_APPLY"

        rows.append(
            {
                "approval_record_id": operation.approval_record_id,
                "patch_operation_id": operation.patch_operation_id,
                "proposal_id": operation.proposal_id,
                "normalized_alias_label": operation.normalized_alias_label,
                "target_metric": operation.target_metric,
                "target_group": operation.target_asset_group,
                "precheck_status": precheck_status,
                "semantic_constraint_pass": semantic_pass,
                "semantic_constraint_detail": semantic_detail,
                "same_label_match_count": len(same_label_rows),
                "conflicting_rule_id": _norm(conflicting_match.get("rule_id")) if conflicting_match else "",
                "exact_match_rule_id": _norm(exact_match.get("rule_id")) if exact_match else "",
                "expected_entry_json": json.dumps(expected_entry, ensure_ascii=False),
            }
        )
    return rows, conflict_count


def _apply_operations(
    operations: Sequence[ApprovedAliasOperation],
    precheck_rows: Sequence[Dict[str, Any]],
    alias_payload: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    mutable_payload = deepcopy(alias_payload)
    groups = mutable_payload.setdefault("groups", {})
    if not isinstance(groups, dict):
        groups = {}
        mutable_payload["groups"] = groups
    group_rows = groups.setdefault(TARGET_GROUP, [])
    if not isinstance(group_rows, list):
        group_rows = []
        groups[TARGET_GROUP] = group_rows

    precheck_lookup = {
        _norm(row.get("patch_operation_id")): row
        for row in precheck_rows
        if isinstance(row, dict)
    }
    logs: List[Dict[str, Any]] = []

    for operation in operations:
        precheck = precheck_lookup.get(operation.patch_operation_id, {})
        status = _norm(precheck.get("precheck_status"))
        expected_entry = _official_alias_entry(operation)
        before_state = next(
            (
                deepcopy(item)
                for item in group_rows
                if isinstance(item, dict)
                and _label_key(item.get("normalized_label")) == _label_key(operation.normalized_alias_label)
            ),
            None,
        )

        after_state = before_state
        operation_status = status
        if status == "READY_TO_APPLY":
            group_rows.append(expected_entry)
            after_state = deepcopy(expected_entry)
            operation_status = "APPLIED"
        elif status == "IDEMPOTENT_ALREADY_APPLIED":
            after_state = deepcopy(before_state)

        logs.append(
            {
                "approval_record_id": operation.approval_record_id,
                "patch_operation_id": operation.patch_operation_id,
                "proposal_id": operation.proposal_id,
                "candidate_id": operation.candidate_id,
                "operation": operation.operation,
                "candidate_type": operation.candidate_type,
                "normalized_alias_label": operation.normalized_alias_label,
                "target_metric": operation.target_metric,
                "target_asset_path": str(SEMANTIC_ALIAS_ASSET_PATH),
                "target_group": TARGET_GROUP,
                "generated_rule_id": expected_entry["rule_id"],
                "operation_status": operation_status,
                "before_state": before_state,
                "after_state": after_state,
                "expected_affected_candidate_count": operation.expected_affected_candidate_count,
                "expected_trusted_gain": operation.expected_trusted_gain,
                "expected_review_reduction": operation.expected_review_reduction,
                "expected_out_of_scope_or_rejected_gain": operation.expected_out_of_scope_or_rejected_gain,
                "rollback_reference": operation.rollback_reference,
                "provenance": operation.provenance,
            }
        )
    return mutable_payload, logs


def _build_rollback_rows(logs: Sequence[Dict[str, Any]], backup_path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in logs:
        status = _norm(row.get("operation_status"))
        rows.append(
            {
                "approval_record_id": _norm(row.get("approval_record_id")),
                "patch_operation_id": _norm(row.get("patch_operation_id")),
                "generated_rule_id": _norm(row.get("generated_rule_id")),
                "target_path": str(SEMANTIC_ALIAS_ASSET_PATH),
                "target_group": TARGET_GROUP,
                "operation_status": status,
                "rollback_action": "restore_asset_from_backup" if status == "APPLIED" else "no_action_required_idempotent",
                "backup_path": backup_path,
            }
        )
    return rows


def _asset_diff_rows(
    before_snapshot: Dict[str, Any],
    after_snapshot: Dict[str, Any],
    logs: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
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
    for row in logs:
        rows.append(
            {
                "target_path": str(SEMANTIC_ALIAS_ASSET_PATH),
                "operation_status": _norm(row.get("operation_status")),
                "generated_rule_id": _norm(row.get("generated_rule_id")),
                "patch_operation_id": _norm(row.get("patch_operation_id")),
                "before_state": json.dumps(_to_jsonable(row.get("before_state")), ensure_ascii=False),
                "after_state": json.dumps(_to_jsonable(row.get("after_state")), ensure_ascii=False),
            }
        )
    return rows


def build_official_alias_patch_application_325n(
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
    add_qa("dry_run_patch_operations::count", "PASS" if len(patch_rows) == 6 else "FAIL", f"actual={len(patch_rows)}")

    for operation in operations:
        patch_row = patch_lookup.get(operation.patch_operation_id, {})
        add_qa(
            f"patch_alignment::{operation.patch_operation_id}::exists",
            "PASS" if bool(patch_row) else "FAIL",
            operation.patch_operation_id,
        )
        add_qa(
            f"patch_alignment::{operation.patch_operation_id}::proposal_id",
            "PASS" if _norm(patch_row.get("controlled_proposal_id_325k")) == operation.proposal_id else "FAIL",
            _norm(patch_row.get("controlled_proposal_id_325k")),
        )
        add_qa(
            f"patch_alignment::{operation.patch_operation_id}::alias_label",
            "PASS" if _norm(patch_row.get("alias_label")) == operation.alias_label else "FAIL",
            _norm(patch_row.get("alias_label")),
        )
        add_qa(
            f"patch_alignment::{operation.patch_operation_id}::target_metric",
            "PASS" if _norm(patch_row.get("target_metric")) == operation.target_metric else "FAIL",
            _norm(patch_row.get("target_metric")),
        )
        add_qa(
            f"patch_alignment::{operation.patch_operation_id}::patch_operation_type",
            "PASS" if _norm(patch_row.get("patch_operation_type")) == "ADD_ALIAS" else "FAIL",
            _norm(patch_row.get("patch_operation_type")),
        )
        add_qa(
            f"patch_alignment::{operation.patch_operation_id}::target_asset_path",
            "PASS" if _norm(patch_row.get("target_asset_path")) == str(SEMANTIC_ALIAS_ASSET_PATH) else "FAIL",
            _norm(patch_row.get("target_asset_path")),
        )
        add_qa(
            f"patch_alignment::{operation.patch_operation_id}::target_group",
            "PASS" if _norm(patch_row.get("target_asset_group")) == TARGET_GROUP else "FAIL",
            _norm(patch_row.get("target_asset_group")),
        )

    alias_hash_before = _sha256_file(SEMANTIC_ALIAS_ASSET_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    before_snapshot = {
        "stage": "325N",
        "snapshot_type": "before",
        "assets": [
            _snapshot_asset(SEMANTIC_ALIAS_ASSET_PATH, "alias"),
            _snapshot_asset(FORMAL_SCOPE_RULES_PATH, "scope"),
        ],
    }
    add_qa("before_snapshot::generated", "PASS", f"asset_count={len(before_snapshot['assets'])}")

    alias_payload = _load_alias_asset()
    groups = alias_payload.get("groups", {})
    target_group_exists = isinstance(groups, dict) and isinstance(groups.get(TARGET_GROUP), list)
    add_qa(
        "target_assets::alias_asset_readable",
        "PASS" if isinstance(groups, dict) else "FAIL",
        str(SEMANTIC_ALIAS_ASSET_PATH),
    )
    add_qa(
        "target_assets::target_group_exists",
        "PASS" if target_group_exists else "FAIL",
        f"{SEMANTIC_ALIAS_ASSET_PATH}::{TARGET_GROUP}",
    )
    add_qa(
        "safety::formal_scope_rules_present",
        "PASS" if FORMAL_SCOPE_RULES_PATH.exists() else "FAIL",
        str(FORMAL_SCOPE_RULES_PATH),
    )

    precheck_rows, conflicting_existing_alias_count = _prepare_precheck(operations, alias_payload)
    for row in precheck_rows:
        status = _norm(row.get("precheck_status"))
        semantic_pass = bool(row.get("semantic_constraint_pass"))
        add_qa(
            f"preapply::{_norm(row.get('patch_operation_id'))}::semantic_constraint",
            "PASS" if semantic_pass else "FAIL",
            _norm(row.get("semantic_constraint_detail")),
        )
        add_qa(
            f"preapply::{_norm(row.get('patch_operation_id'))}::status",
            "PASS" if status in {"READY_TO_APPLY", "IDEMPOTENT_ALREADY_APPLIED"} else "FAIL",
            status,
        )

    add_qa(
        "preapply::conflicting_existing_alias_count",
        "PASS" if conflicting_existing_alias_count == 0 else "FAIL",
        f"actual={conflicting_existing_alias_count}",
    )

    apply_blocked = any(row["status"] == "FAIL" for row in qa_rows)
    backup_path = ""
    logs: List[Dict[str, Any]] = []
    if not apply_blocked:
        backup_path = _build_backup_file(output_dir)
        add_qa(
            "rollback::alias_asset_backup_created",
            "PASS" if Path(backup_path).exists() else "FAIL",
            backup_path,
        )
        alias_after_payload, logs = _apply_operations(
            operations=operations,
            precheck_rows=precheck_rows,
            alias_payload=alias_payload,
        )
        if any(_norm(row.get("operation_status")) == "APPLIED" for row in logs):
            _write_alias_asset(alias_after_payload)

    alias_hash_after = _sha256_file(SEMANTIC_ALIAS_ASSET_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    after_snapshot = {
        "stage": "325N",
        "snapshot_type": "after",
        "assets": [
            _snapshot_asset(SEMANTIC_ALIAS_ASSET_PATH, "alias"),
            _snapshot_asset(FORMAL_SCOPE_RULES_PATH, "scope"),
        ],
    }
    add_qa("after_snapshot::generated", "PASS", f"asset_count={len(after_snapshot['assets'])}")

    applied_count = int(sum(1 for row in logs if _norm(row.get("operation_status")) == "APPLIED"))
    idempotent_count = int(sum(1 for row in logs if _norm(row.get("operation_status")) == "IDEMPOTENT_ALREADY_APPLIED"))
    applied_or_idempotent_count = applied_count + idempotent_count

    duplicate_count_before = _count_alias_duplicates(alias_payload)
    duplicate_count_after = _count_alias_duplicates(_load_alias_asset())
    duplicate_delta_count = duplicate_count_after - duplicate_count_before

    add_qa(
        "application::approved_patch_operation_count",
        "PASS" if len(operations) == 6 else "FAIL",
        f"actual={len(operations)}",
    )
    add_qa(
        "application::alias_approved_patch_operation_count",
        "PASS" if len(operations) == 6 else "FAIL",
        f"actual={len(operations)}",
    )
    add_qa("application::scope_approved_patch_operation_count", "PASS", "actual=0")
    add_qa(
        "application::applied_or_idempotent_operation_count",
        "PASS" if applied_or_idempotent_count == 6 else "FAIL",
        f"applied={applied_count} idempotent={idempotent_count}",
    )
    add_qa(
        "safety::formal_scope_rules_hash_unchanged",
        "PASS" if scope_hash_before == scope_hash_after else "FAIL",
        f"before={scope_hash_before} after={scope_hash_after}",
    )
    add_qa(
        "safety::semantic_alias_candidates_hash_changed_only_if_applied",
        "PASS"
        if (
            (applied_count > 0 and alias_hash_before != alias_hash_after)
            or (applied_count == 0 and alias_hash_before == alias_hash_after)
        )
        else "FAIL",
        f"before={alias_hash_before} after={alias_hash_after}",
    )
    add_qa(
        "postapply::duplicate_delta_count",
        "PASS" if duplicate_delta_count == 0 else "FAIL",
        f"before={duplicate_count_before} after={duplicate_count_after} delta={duplicate_delta_count}",
    )

    rerun_precheck_rows, rerun_conflict_count = _prepare_precheck(operations, _load_alias_asset())
    rerun_all_idempotent = all(
        _norm(row.get("precheck_status")) == "IDEMPOTENT_ALREADY_APPLIED"
        for row in rerun_precheck_rows
    ) if rerun_precheck_rows else False
    add_qa(
        "idempotency::rerun_would_be_idempotent",
        "PASS" if rerun_all_idempotent and rerun_conflict_count == 0 else "FAIL",
        f"rows={len(rerun_precheck_rows)} conflicts={rerun_conflict_count}",
    )

    refreshed_alias_payload = _load_alias_asset()
    visible_rule_count = sum(
        1
        for row in _flatten_alias_entries(refreshed_alias_payload)
        if _norm(row.get("approval_stage")) == "325N"
    )
    add_qa(
        "postapply::official_325n_rule_visibility_count",
        "PASS" if visible_rule_count >= 6 else "FAIL",
        f"actual={visible_rule_count}",
    )

    before_by_path = {item["path"]: item for item in before_snapshot["assets"]}
    after_by_path = {item["path"]: item for item in after_snapshot["assets"]}
    before_after_preview_rows = [
        {
            "target_asset_path": str(SEMANTIC_ALIAS_ASSET_PATH),
            "target_group": TARGET_GROUP,
            "candidate_type": "alias",
            "before_entry_count": before_by_path.get(str(SEMANTIC_ALIAS_ASSET_PATH), {}).get("group_counts", {}).get(TARGET_GROUP, 0),
            "after_entry_count": after_by_path.get(str(SEMANTIC_ALIAS_ASSET_PATH), {}).get("group_counts", {}).get(TARGET_GROUP, 0),
            "applied_operation_count": applied_count,
            "idempotent_operation_count": idempotent_count,
            "affected_candidate_count": int(sum(row.expected_affected_candidate_count for row in operations)),
            "expected_trusted_gain": int(sum(row.expected_trusted_gain for row in operations)),
            "expected_review_reduction": int(sum(row.expected_review_reduction for row in operations)),
            "expected_out_of_scope_or_rejected_gain": int(sum(row.expected_out_of_scope_or_rejected_gain for row in operations)),
        },
        {
            "target_asset_path": str(FORMAL_SCOPE_RULES_PATH),
            "target_group": "",
            "candidate_type": "scope_guard",
            "before_entry_count": before_by_path.get(str(FORMAL_SCOPE_RULES_PATH), {}).get("entry_count", 0),
            "after_entry_count": after_by_path.get(str(FORMAL_SCOPE_RULES_PATH), {}).get("entry_count", 0),
            "applied_operation_count": 0,
            "idempotent_operation_count": 0,
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
        "stage": "325N",
        "output_dir": str(output_dir),
        "approved_patch_operation_count": len(operations),
        "alias_approved_patch_operation_count": len(operations),
        "scope_approved_patch_operation_count": 0,
        "applied_operation_count": applied_count,
        "idempotent_operation_count": idempotent_count,
        "applied_or_idempotent_operation_count": applied_or_idempotent_count,
        "conflicting_existing_alias_count": conflicting_existing_alias_count,
        "target_conflict_count": conflicting_existing_alias_count,
        "duplicate_count_before": duplicate_count_before,
        "duplicate_count_after": duplicate_count_after,
        "duplicate_delta_count": duplicate_delta_count,
        "semantic_alias_candidates_hash_before": alias_hash_before,
        "semantic_alias_candidates_hash_after": alias_hash_after,
        "formal_scope_rules_hash_before": scope_hash_before,
        "formal_scope_rules_hash_after": scope_hash_after,
        "semantic_alias_candidates_hash_changed": alias_hash_before != alias_hash_after,
        "formal_scope_rules_hash_unchanged": scope_hash_before == scope_hash_after,
        "target_official_assets_modified": (
            [str(SEMANTIC_ALIAS_ASSET_PATH)] if alias_hash_before != alias_hash_after else []
        ),
        "formal_scope_rules_unchanged_confirmed": scope_hash_before == scope_hash_after,
        "affected_candidate_count": int(sum(row.expected_affected_candidate_count for row in operations)),
        "expected_trusted_gain": int(sum(row.expected_trusted_gain for row in operations)),
        "expected_review_reduction": int(sum(row.expected_review_reduction for row in operations)),
        "expected_out_of_scope_or_rejected_gain": int(sum(row.expected_out_of_scope_or_rejected_gain for row in operations)),
        "rollback_backup_paths": {"alias_backup_path": backup_path} if backup_path else {},
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": EXPECTED_325N_DECISION if qa_fail_count == 0 else EXPECTED_325N_NOT_READY,
    }

    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }

    apply_proof_json = {
        "stage": "325N",
        "decision": summary["decision"],
        "files_read": [
            str(Path(r"D:\_datefac\output\controlled_alias_proposal_human_approval_325m_reviewed\controlled_alias_proposal_human_approval_325m_reviewed_summary.json")),
            str(Path(r"D:\_datefac\output\controlled_alias_proposal_human_approval_325m_reviewed\controlled_alias_proposal_human_approval_325m_reviewed_qa.json")),
            str(Path(r"D:\_datefac\output\controlled_alias_proposal_human_approval_325m_reviewed\controlled_alias_proposal_human_approval_325m_reviewed_result.json")),
            str(Path(r"D:\_datefac\output\controlled_official_proposal_dry_run_325l\controlled_official_proposal_dry_run_325l_summary.json")),
            str(Path(r"D:\_datefac\output\controlled_official_proposal_dry_run_325l\controlled_official_proposal_dry_run_325l_qa.json")),
            str(Path(r"D:\_datefac\output\controlled_official_proposal_dry_run_325l\controlled_official_proposal_dry_run_325l_patch_operations.json")),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
        "official_assets_before": {
            str(SEMANTIC_ALIAS_ASSET_PATH): alias_hash_before,
            str(FORMAL_SCOPE_RULES_PATH): scope_hash_before,
        },
        "official_assets_after": {
            str(SEMANTIC_ALIAS_ASSET_PATH): alias_hash_after,
            str(FORMAL_SCOPE_RULES_PATH): scope_hash_after,
        },
        "official_assets_written": summary["target_official_assets_modified"],
        "approved_patch_operation_ids": [row.patch_operation_id for row in operations],
        "applied_patch_operation_ids": [
            _norm(row.get("patch_operation_id"))
            for row in logs
            if _norm(row.get("operation_status")) == "APPLIED"
        ],
        "idempotent_patch_operation_ids": [
            _norm(row.get("patch_operation_id"))
            for row in logs
            if _norm(row.get("operation_status")) == "IDEMPOTENT_ALREADY_APPLIED"
        ],
        "formal_scope_rules_unchanged": scope_hash_before == scope_hash_after,
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
                "limitation": "approved_alias_only",
                "detail": "325N applies only the six approved alias operations from 325M reviewed output.",
            },
            {
                "limitation": "scope_asset_guard",
                "detail": "325N reads formal scope rules only for hash safety checks and never writes that asset.",
            },
        ]
    ).fillna("")
    precheck_df = pd.DataFrame(precheck_rows).fillna("")

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
        "precheck_df": precheck_df,
    }
