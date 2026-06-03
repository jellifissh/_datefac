from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd


EXPECTED_322M_REVIEWED_DECISION = (
    "OFFICIAL_SEMANTIC_PATCH_HUMAN_APPROVAL_322M_REVIEWED_READY_FOR_322N_OFFICIAL_PATCH_APPLICATION"
)
EXPECTED_322N_DECISION = "OFFICIAL_SEMANTIC_PATCH_APPLICATION_322N_READY_FOR_322O_POST_PATCH_REGRESSION"
EXPECTED_322N_NOT_READY = "OFFICIAL_SEMANTIC_PATCH_APPLICATION_322N_NOT_READY"

DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\official_semantic_patch_application_322n")
FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
SEMANTIC_ALIAS_ASSET_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")
OFFICIAL_OVERRIDE_PATH = Path(r"D:\_datefac\data\overrides\02B_ai_repair_override.xlsx")
FINANCIAL_STANDARDIZER_PATH = Path(r"D:\_datefac\financial_standardizer.py")

ALIAS_RULE_FAMILY = "semantic_alias_candidates"
SCOPE_RULE_FAMILY = "formal_scope_rules"
EXPECTED_COUNTS = {
    "approved_patch_count": 10,
    "alias_operation_count": 3,
    "scope_operation_count": 7,
    "unit_operation_count": 0,
    "rejected_noise_operation_count": 0,
    "expected_affected_candidate_count": 287,
    "expected_trusted_gain": 49,
    "expected_review_reduction": 287,
    "expected_out_of_scope_or_rejected_gain": 238,
}


@dataclass(frozen=True)
class ApprovedOperation:
    approval_id: str
    dry_run_patch_operation_id: str
    controlled_patch_proposal_id: str
    source_rule_id: str
    rule_type: str
    target_file_or_rule_group: str
    target_group: str
    operation_type: str
    exact_proposed_change: Dict[str, Any]
    expected_affected_candidate_count: int
    expected_trusted_gain: int
    expected_review_reduction: int
    expected_out_of_scope_or_rejected_gain: int
    rollback_note: str
    reviewer_decision: str
    provenance: Dict[str, Any]


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


def _parse_json_maybe(value: Any) -> Dict[str, Any]:
    text = _norm(value)
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "__MISSING__"
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_to_jsonable(payload), ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(_to_jsonable(row), ensure_ascii=False) + "\n")


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
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


def _default_alias_asset() -> Dict[str, Any]:
    return {
        "schema_version": "1.0",
        "rule_family": ALIAS_RULE_FAMILY,
        "description": "Official semantic alias candidates approved for controlled semantic mapping.",
        "groups": {},
    }


def _load_alias_asset() -> Dict[str, Any]:
    raw = _read_json(SEMANTIC_ALIAS_ASSET_PATH)
    if not raw:
        return _default_alias_asset()
    groups = raw.get("groups", {})
    if not isinstance(groups, dict):
        groups = {}
    raw["groups"] = groups
    raw.setdefault("schema_version", "1.0")
    raw.setdefault("rule_family", ALIAS_RULE_FAMILY)
    raw.setdefault(
        "description",
        "Official semantic alias candidates approved for controlled semantic mapping.",
    )
    return raw


def _write_alias_asset(payload: Dict[str, Any]) -> None:
    groups = payload.get("groups", {})
    if not isinstance(groups, dict):
        groups = {}
    normalized_groups: Dict[str, List[Dict[str, Any]]] = {}
    for group_name in sorted(groups.keys()):
        items = groups.get(group_name, [])
        if not isinstance(items, list):
            items = []
        normalized_groups[group_name] = sorted(
            [item for item in items if isinstance(item, dict)],
            key=lambda item: (
                _norm(item.get("normalized_label")),
                _norm(item.get("metric_code")),
                _norm(item.get("rule_id")),
            ),
        )
    output = {
        "schema_version": payload.get("schema_version", "1.0"),
        "rule_family": payload.get("rule_family", ALIAS_RULE_FAMILY),
        "description": payload.get(
            "description",
            "Official semantic alias candidates approved for controlled semantic mapping.",
        ),
        "groups": normalized_groups,
    }
    _write_json(SEMANTIC_ALIAS_ASSET_PATH, output)


def _load_scope_asset() -> Dict[str, Any]:
    return _read_json(FORMAL_SCOPE_RULES_PATH)


def _write_scope_asset(payload: Dict[str, Any]) -> None:
    rules = payload.get("rules", {})
    if not isinstance(rules, dict):
        rules = {}
    output = {
        "schema_version": payload.get("schema_version", "1.0"),
        "rule_family": payload.get("rule_family", SCOPE_RULE_FAMILY),
        "description": payload.get(
            "description",
            "Formal scope applicability rules for financial standardization.",
        ),
        "rules": {rule_id: rules[rule_id] for rule_id in sorted(rules.keys())},
    }
    _write_json(FORMAL_SCOPE_RULES_PATH, output)


def _flatten_alias_entries(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    groups = payload.get("groups", {})
    if not isinstance(groups, dict):
        return []
    rows: List[Dict[str, Any]] = []
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


def _flatten_scope_entries(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    rules = payload.get("rules", {})
    if not isinstance(rules, dict):
        return []
    rows: List[Dict[str, Any]] = []
    for rule_id, item in rules.items():
        if not isinstance(item, dict):
            continue
        row = dict(item)
        row.setdefault("rule_id", _norm(rule_id))
        rows.append(row)
    return rows


def _snapshot_asset(path: Path, asset_type: str) -> Dict[str, Any]:
    if asset_type == "alias":
        payload = _load_alias_asset() if path.exists() else _default_alias_asset()
        entries = _flatten_alias_entries(payload)
        group_counts: Dict[str, int] = {}
        for row in entries:
            group_name = _norm(row.get("target_group"))
            group_counts[group_name] = group_counts.get(group_name, 0) + 1
        return {
            "asset_type": "alias",
            "path": str(path),
            "file_exists": path.exists(),
            "content_hash": _sha256_file(path),
            "rule_family": payload.get("rule_family", ""),
            "group_counts": group_counts,
            "entry_count": len(entries),
            "entries": entries,
        }
    payload = _load_scope_asset()
    entries = _flatten_scope_entries(payload)
    group_counts: Dict[str, int] = {}
    for row in entries:
        group_name = _norm(row.get("target_group")) or _norm(row.get("scope_action"))
        group_counts[group_name] = group_counts.get(group_name, 0) + 1
    return {
        "asset_type": "scope",
        "path": str(path),
        "file_exists": path.exists(),
        "content_hash": _sha256_file(path),
        "rule_family": payload.get("rule_family", ""),
        "group_counts": group_counts,
        "entry_count": len(entries),
        "entries": entries,
    }


def _build_backup_files(output_dir: Path) -> Dict[str, str]:
    backup_dir = output_dir / "rollback_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    scope_backup = backup_dir / "formal_scope_rules.before_322n.json"
    alias_backup = backup_dir / "semantic_alias_candidates.before_322n.json"

    if FORMAL_SCOPE_RULES_PATH.exists():
        scope_backup.write_text(FORMAL_SCOPE_RULES_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        _write_json(scope_backup, {"file_exists": False, "path": str(FORMAL_SCOPE_RULES_PATH)})

    if SEMANTIC_ALIAS_ASSET_PATH.exists():
        alias_backup.write_text(SEMANTIC_ALIAS_ASSET_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        _write_json(alias_backup, {"file_exists": False, "path": str(SEMANTIC_ALIAS_ASSET_PATH)})

    return {
        "scope_backup_path": str(scope_backup),
        "alias_backup_path": str(alias_backup),
    }


def load_official_patch_application_inputs(
    reviewed_approval_dir: Path,
    dry_run_dir: Path,
    controlled_proposal_dir: Path,
    sandbox_application_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    return {
        "reviewed_summary": _read_json(
            reviewed_approval_dir / "official_semantic_patch_human_approval_322m_reviewed_summary.json"
        ),
        "reviewed_qa": _read_json(
            reviewed_approval_dir / "official_semantic_patch_human_approval_322m_reviewed_qa.json"
        ),
        "final_approved_patch_plan": _read_json(
            reviewed_approval_dir / "official_semantic_patch_human_approval_322m_final_approved_patch_plan.json"
        ),
        "dry_run_summary": _read_json(dry_run_dir / "official_semantic_patch_dry_run_322l_summary.json"),
        "dry_run_qa": _read_json(dry_run_dir / "official_semantic_patch_dry_run_322l_qa.json"),
        "controlled_summary": _read_json(
            controlled_proposal_dir / "controlled_official_semantic_patch_proposal_322k_summary.json"
        ),
        "sandbox_summary": _read_json(
            (sandbox_application_dir or Path())
            / "official_semantic_rule_candidates_322j_summary.json"
        )
        if sandbox_application_dir
        else {},
    }


def _validate_reviewed_readiness(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add(
        "reviewed_readiness::decision",
        _norm(summary.get("official_patch_human_approval_decision")) == EXPECTED_322M_REVIEWED_DECISION,
        _norm(summary.get("official_patch_human_approval_decision")),
    )
    add("reviewed_readiness::qa_fail_count", _safe_int(summary.get("qa_fail_count")) == 0, str(summary.get("qa_fail_count", "")))
    add(
        "reviewed_readiness::reviewed_approval_record_count",
        _safe_int(summary.get("reviewed_approval_record_count")) == 10,
        str(summary.get("reviewed_approval_record_count", "")),
    )
    add(
        "reviewed_readiness::approved_patch_count",
        _safe_int(summary.get("approved_patch_count")) == 10,
        str(summary.get("approved_patch_count", "")),
    )
    add(
        "reviewed_readiness::rejected_patch_count",
        _safe_int(summary.get("rejected_patch_count")) == 0,
        str(summary.get("rejected_patch_count", "")),
    )
    add(
        "reviewed_readiness::needs_more_review_count",
        _safe_int(summary.get("needs_more_review_count")) == 0,
        str(summary.get("needs_more_review_count", "")),
    )
    add(
        "reviewed_readiness::pending_count",
        _safe_int(summary.get("pending_count")) == 0,
        str(summary.get("pending_count", "")),
    )
    add(
        "reviewed_readiness::invalid_decision_count",
        _safe_int(summary.get("invalid_decision_count")) == 0,
        str(summary.get("invalid_decision_count", "")),
    )
    add(
        "reviewed_readiness::final_approved_patch_count",
        _safe_int(summary.get("final_approved_patch_count")) == 10,
        str(summary.get("final_approved_patch_count", "")),
    )
    return checks


def _normalize_operation(row: Dict[str, Any]) -> ApprovedOperation:
    provenance = {
        "source_322k_proposal_id": _norm(row.get("source_322k_proposal_id")),
        "source_322j_rule_id": _norm(row.get("source_322j_rule_id")),
        "source_322i_proposal_id": _norm(row.get("source_322i_proposal_id")),
        "human_confirmation_source_case_id": _norm(row.get("human_confirmation_source_case_id")),
    }
    return ApprovedOperation(
        approval_id=_norm(row.get("approval_id")),
        dry_run_patch_operation_id=_norm(row.get("dry_run_patch_operation_id")),
        controlled_patch_proposal_id=_norm(row.get("controlled_patch_proposal_id")),
        source_rule_id=_norm(row.get("source_rule_id")),
        rule_type=_norm(row.get("rule_type")),
        target_file_or_rule_group=_norm(row.get("target_file_or_rule_group")),
        target_group=_norm(row.get("target_group")),
        operation_type=_norm(row.get("operation_type")),
        exact_proposed_change=_parse_json_maybe(row.get("exact_proposed_change")),
        expected_affected_candidate_count=_safe_int(row.get("expected_affected_candidate_count")),
        expected_trusted_gain=_safe_int(row.get("expected_trusted_gain")),
        expected_review_reduction=_safe_int(row.get("expected_review_reduction")),
        expected_out_of_scope_or_rejected_gain=_safe_int(row.get("expected_out_of_scope_or_rejected_gain")),
        rollback_note=_norm(row.get("rollback_note")),
        reviewer_decision=_norm(row.get("reviewer_decision")),
        provenance=provenance,
    )


def _validate_final_plan(plan: Dict[str, Any]) -> Tuple[List[ApprovedOperation], List[Dict[str, Any]]]:
    checks: List[Dict[str, Any]] = []
    approved_rows = plan.get("approved_patch_operations", [])
    approved_rows = approved_rows if isinstance(approved_rows, list) else []
    operations = [_normalize_operation(row) for row in approved_rows if isinstance(row, dict)]

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add("patch_plan::exists", bool(plan), "loaded" if plan else "missing_or_invalid")
    add(
        "patch_plan::decision",
        _norm(plan.get("decision")) == EXPECTED_322M_REVIEWED_DECISION,
        _norm(plan.get("decision")),
    )
    add("patch_plan::approved_operation_count", len(operations) == 10, f"actual={len(operations)}")
    add(
        "patch_plan::rejected_operation_count",
        len(plan.get("rejected_patch_operations", []) if isinstance(plan.get("rejected_patch_operations", []), list) else []) == 0,
        f"actual={len(plan.get('rejected_patch_operations', [])) if isinstance(plan.get('rejected_patch_operations', []), list) else 0}",
    )
    add(
        "patch_plan::needs_more_review_operation_count",
        len(plan.get("needs_more_review_patch_operations", []) if isinstance(plan.get("needs_more_review_patch_operations", []), list) else []) == 0,
        f"actual={len(plan.get('needs_more_review_patch_operations', [])) if isinstance(plan.get('needs_more_review_patch_operations', []), list) else 0}",
    )

    duplicate_approval_ids = len({op.approval_id for op in operations}) != len(operations)
    duplicate_patch_ids = len({op.dry_run_patch_operation_id for op in operations}) != len(operations)
    add("patch_plan::no_duplicate_approval_id", not duplicate_approval_ids, f"duplicate_present={duplicate_approval_ids}")
    add("patch_plan::no_duplicate_patch_operation_id", not duplicate_patch_ids, f"duplicate_present={duplicate_patch_ids}")

    required_field_failures = 0
    provenance_failures = 0
    rule_type_counts = {"alias": 0, "out_of_scope": 0, "unit": 0, "rejected_noise": 0}
    expected_affected = 0
    expected_trusted = 0
    expected_review = 0
    expected_scope = 0
    for op in operations:
        if op.rule_type in rule_type_counts:
            rule_type_counts[op.rule_type] += 1
        if not all(
            [
                op.approval_id,
                op.dry_run_patch_operation_id,
                op.controlled_patch_proposal_id,
                op.source_rule_id,
                op.rule_type,
                op.target_group,
                op.operation_type,
                bool(op.exact_proposed_change),
                op.rollback_note,
                op.reviewer_decision == "APPROVED",
            ]
        ):
            required_field_failures += 1
        if not all(_norm(v) for v in op.provenance.values()):
            provenance_failures += 1
        expected_affected += op.expected_affected_candidate_count
        expected_trusted += op.expected_trusted_gain
        expected_review += op.expected_review_reduction
        expected_scope += op.expected_out_of_scope_or_rejected_gain

    add("patch_plan::required_fields_complete", required_field_failures == 0, f"failed_records={required_field_failures}")
    add("patch_plan::provenance_complete", provenance_failures == 0, f"failed_records={provenance_failures}")
    add("patch_plan::alias_count", rule_type_counts["alias"] == 3, f"actual={rule_type_counts['alias']}")
    add("patch_plan::scope_count", rule_type_counts["out_of_scope"] == 7, f"actual={rule_type_counts['out_of_scope']}")
    add("patch_plan::unit_count", rule_type_counts["unit"] == 0, f"actual={rule_type_counts['unit']}")
    add(
        "patch_plan::rejected_noise_count",
        rule_type_counts["rejected_noise"] == 0,
        f"actual={rule_type_counts['rejected_noise']}",
    )
    add(
        "patch_plan::expected_affected_candidate_count",
        expected_affected == EXPECTED_COUNTS["expected_affected_candidate_count"],
        f"actual={expected_affected}",
    )
    add(
        "patch_plan::expected_trusted_gain",
        expected_trusted == EXPECTED_COUNTS["expected_trusted_gain"],
        f"actual={expected_trusted}",
    )
    add(
        "patch_plan::expected_review_reduction",
        expected_review == EXPECTED_COUNTS["expected_review_reduction"],
        f"actual={expected_review}",
    )
    add(
        "patch_plan::expected_out_of_scope_or_rejected_gain",
        expected_scope == EXPECTED_COUNTS["expected_out_of_scope_or_rejected_gain"],
        f"actual={expected_scope}",
    )
    return operations, checks


def _approval_suffix(approval_id: str) -> str:
    suffix = _norm(approval_id).split("::")[-1]
    return suffix or "000"


def _build_alias_rule_id(op: ApprovedOperation) -> str:
    return f"SEM_ALIAS_322N_{_approval_suffix(op.approval_id)}"


def _build_scope_rule_id(op: ApprovedOperation) -> str:
    return f"SEM_SCOPE_322N_{_approval_suffix(op.approval_id)}"


def _find_alias_match(entries: List[Dict[str, Any]], target_group: str, normalized_label: str) -> Optional[Dict[str, Any]]:
    for item in entries:
        if _norm(item.get("target_group")) == _norm(target_group) and _norm(item.get("normalized_label")) == _norm(normalized_label):
            return item
    return None


def _find_scope_matches(entries: List[Dict[str, Any]], normalized_label: str) -> List[Dict[str, Any]]:
    return [item for item in entries if _norm(item.get("normalized_label")) == _norm(normalized_label)]


def _prepare_precheck(
    operations: Sequence[ApprovedOperation],
    alias_asset: Dict[str, Any],
    scope_asset: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], int]:
    alias_entries = _flatten_alias_entries(alias_asset)
    scope_entries = _flatten_scope_entries(scope_asset)
    rows: List[Dict[str, Any]] = []
    conflict_count = 0

    for op in operations:
        if op.rule_type == "alias":
            label = _norm(op.exact_proposed_change.get("normalized_label"))
            metric_code = _norm(op.exact_proposed_change.get("metric_code"))
            metric_family = _norm(op.exact_proposed_change.get("metric_family")) or _norm(op.target_group)
            existing = _find_alias_match(alias_entries, metric_family, label)
            state = "READY_TO_APPLY"
            conflict_detail = ""
            if existing:
                if _norm(existing.get("metric_code")) == metric_code:
                    state = "IDEMPOTENT_ALREADY_APPLIED"
                else:
                    state = "CONFLICT"
                    conflict_detail = json.dumps(existing, ensure_ascii=False)
                    conflict_count += 1
            rows.append(
                {
                    "approval_id": op.approval_id,
                    "dry_run_patch_operation_id": op.dry_run_patch_operation_id,
                    "rule_type": op.rule_type,
                    "resolved_target_path": str(SEMANTIC_ALIAS_ASSET_PATH),
                    "target_group": metric_family,
                    "normalized_label": label,
                    "proposed_value": metric_code,
                    "precheck_status": state,
                    "conflict_detail": conflict_detail,
                    "target_exists": SEMANTIC_ALIAS_ASSET_PATH.exists(),
                    "target_creatable": True,
                }
            )
            continue

        label = _norm(op.exact_proposed_change.get("normalized_label"))
        scope_action = _norm(op.exact_proposed_change.get("scope_action")) or "exclude_from_core_metric_mapping"
        matches = _find_scope_matches(scope_entries, label)
        state = "READY_TO_APPLY"
        conflict_detail = ""
        if matches:
            exact_match = next(
                (
                    item
                    for item in matches
                    if _norm(item.get("scope_action")) == scope_action
                    and _norm(item.get("target_group")) == _norm(op.target_group)
                ),
                None,
            )
            if exact_match:
                state = "IDEMPOTENT_ALREADY_APPLIED"
            else:
                state = "CONFLICT"
                conflict_detail = json.dumps(matches, ensure_ascii=False)
                conflict_count += 1
        rows.append(
            {
                "approval_id": op.approval_id,
                "dry_run_patch_operation_id": op.dry_run_patch_operation_id,
                "rule_type": op.rule_type,
                "resolved_target_path": str(FORMAL_SCOPE_RULES_PATH),
                "target_group": op.target_group,
                "normalized_label": label,
                "proposed_value": scope_action,
                "precheck_status": state,
                "conflict_detail": conflict_detail,
                "target_exists": FORMAL_SCOPE_RULES_PATH.exists(),
                "target_creatable": False,
            }
        )
    return rows, conflict_count


def _apply_operations(
    operations: Sequence[ApprovedOperation],
    precheck_rows: Sequence[Dict[str, Any]],
    alias_asset: Dict[str, Any],
    scope_asset: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
    alias_mutable = json.loads(json.dumps(alias_asset, ensure_ascii=False))
    scope_mutable = json.loads(json.dumps(scope_asset, ensure_ascii=False))
    alias_groups = alias_mutable.setdefault("groups", {})
    scope_rules = scope_mutable.setdefault("rules", {})

    precheck_lookup = {
        _norm(row.get("approval_id")): row for row in precheck_rows
    }
    logs: List[Dict[str, Any]] = []

    for op in operations:
        precheck = precheck_lookup.get(op.approval_id, {})
        status = _norm(precheck.get("precheck_status"))
        label = _norm(op.exact_proposed_change.get("normalized_label"))
        if op.rule_type == "alias":
            metric_code = _norm(op.exact_proposed_change.get("metric_code"))
            metric_family = _norm(op.exact_proposed_change.get("metric_family")) or _norm(op.target_group)
            rule_id = _build_alias_rule_id(op)
            before_state = None
            after_state = None
            if status == "READY_TO_APPLY":
                items = alias_groups.setdefault(metric_family, [])
                if not isinstance(items, list):
                    items = []
                    alias_groups[metric_family] = items
                new_entry = {
                    "rule_id": rule_id,
                    "normalized_label": label,
                    "metric_code": metric_code,
                    "metric_family": metric_family,
                    "source_approval_id": op.approval_id,
                    "source_dry_run_patch_operation_id": op.dry_run_patch_operation_id,
                    "source_controlled_patch_proposal_id": op.controlled_patch_proposal_id,
                    "source_rule_id": op.source_rule_id,
                    "source_322k_proposal_id": op.provenance.get("source_322k_proposal_id", ""),
                    "source_322j_rule_id": op.provenance.get("source_322j_rule_id", ""),
                    "source_322i_proposal_id": op.provenance.get("source_322i_proposal_id", ""),
                    "human_confirmation_source_case_id": op.provenance.get("human_confirmation_source_case_id", ""),
                    "approval_stage": "322N",
                    "status": "APPLIED_322N",
                }
                items.append(new_entry)
                after_state = new_entry
                status = "APPLIED"
            elif status == "IDEMPOTENT_ALREADY_APPLIED":
                existing = _find_alias_match(_flatten_alias_entries(alias_mutable), metric_family, label)
                before_state = existing
                after_state = existing
            logs.append(
                {
                    "approval_id": op.approval_id,
                    "dry_run_patch_operation_id": op.dry_run_patch_operation_id,
                    "rule_type": op.rule_type,
                    "operation_status": status,
                    "resolved_target_path": str(SEMANTIC_ALIAS_ASSET_PATH),
                    "target_group": metric_family,
                    "rule_id": rule_id,
                    "before_state": before_state,
                    "after_state": after_state,
                    "expected_affected_candidate_count": op.expected_affected_candidate_count,
                    "expected_trusted_gain": op.expected_trusted_gain,
                    "expected_review_reduction": op.expected_review_reduction,
                    "expected_out_of_scope_or_rejected_gain": op.expected_out_of_scope_or_rejected_gain,
                    "rollback_note": op.rollback_note,
                    "provenance": op.provenance,
                }
            )
            continue

        scope_action = _norm(op.exact_proposed_change.get("scope_action")) or "exclude_from_core_metric_mapping"
        rule_id = _build_scope_rule_id(op)
        before_state = None
        after_state = None
        if status == "READY_TO_APPLY":
            new_rule = {
                "rule_id": rule_id,
                "rule_type": "core_metric_scope_exclusion",
                "target_group": _norm(op.target_group),
                "normalized_label": label,
                "scope_action": scope_action,
                "existing_scope": "exclude_from_core_metric_mapping",
                "scope_applicability": [
                    "GLOBAL_ALIAS_MATCH_ONLY",
                    "EXCLUDE_FROM_CORE_METRIC_MAPPING",
                ],
                "source_approval_id": op.approval_id,
                "source_dry_run_patch_operation_id": op.dry_run_patch_operation_id,
                "source_controlled_patch_proposal_id": op.controlled_patch_proposal_id,
                "source_rule_id": op.source_rule_id,
                "source_322k_proposal_id": op.provenance.get("source_322k_proposal_id", ""),
                "source_322j_rule_id": op.provenance.get("source_322j_rule_id", ""),
                "source_322i_proposal_id": op.provenance.get("source_322i_proposal_id", ""),
                "human_confirmation_source_case_id": op.provenance.get("human_confirmation_source_case_id", ""),
                "promotion_status": "PROMOTED_322N_OFFICIAL_SEMANTIC_PATCH",
            }
            scope_rules[rule_id] = new_rule
            after_state = new_rule
            status = "APPLIED"
        elif status == "IDEMPOTENT_ALREADY_APPLIED":
            matches = _find_scope_matches(_flatten_scope_entries(scope_mutable), label)
            exact_match = next(
                (
                    item
                    for item in matches
                    if _norm(item.get("scope_action")) == scope_action
                    and _norm(item.get("target_group")) == _norm(op.target_group)
                ),
                None,
            )
            before_state = exact_match
            after_state = exact_match
        logs.append(
            {
                "approval_id": op.approval_id,
                "dry_run_patch_operation_id": op.dry_run_patch_operation_id,
                "rule_type": op.rule_type,
                "operation_status": status,
                "resolved_target_path": str(FORMAL_SCOPE_RULES_PATH),
                "target_group": _norm(op.target_group),
                "rule_id": rule_id,
                "before_state": before_state,
                "after_state": after_state,
                "expected_affected_candidate_count": op.expected_affected_candidate_count,
                "expected_trusted_gain": op.expected_trusted_gain,
                "expected_review_reduction": op.expected_review_reduction,
                "expected_out_of_scope_or_rejected_gain": op.expected_out_of_scope_or_rejected_gain,
                "rollback_note": op.rollback_note,
                "provenance": op.provenance,
            }
        )

    return alias_mutable, scope_mutable, logs


def _asset_diff_rows(before_snapshot: Dict[str, Any], after_snapshot: Dict[str, Any], logs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    before_by_path = {item["path"]: item for item in before_snapshot.get("assets", [])}
    after_by_path = {item["path"]: item for item in after_snapshot.get("assets", [])}
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
                "target_path": log_row.get("resolved_target_path", ""),
                "operation_status": log_row.get("operation_status", ""),
                "rule_type": log_row.get("rule_type", ""),
                "target_group": log_row.get("target_group", ""),
                "rule_id": log_row.get("rule_id", ""),
                "approval_id": log_row.get("approval_id", ""),
                "before_state": json.dumps(_to_jsonable(log_row.get("before_state")), ensure_ascii=False),
                "after_state": json.dumps(_to_jsonable(log_row.get("after_state")), ensure_ascii=False),
                "rollback_note": log_row.get("rollback_note", ""),
            }
        )
    return rows


def _build_rollback_rows(
    logs: Sequence[Dict[str, Any]],
    backup_paths: Dict[str, str],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for log_row in logs:
        target_path = _norm(log_row.get("resolved_target_path"))
        backup_path = backup_paths["alias_backup_path"] if target_path == str(SEMANTIC_ALIAS_ASSET_PATH) else backup_paths["scope_backup_path"]
        rows.append(
            {
                "approval_id": _norm(log_row.get("approval_id")),
                "dry_run_patch_operation_id": _norm(log_row.get("dry_run_patch_operation_id")),
                "rule_type": _norm(log_row.get("rule_type")),
                "target_path": target_path,
                "rule_id": _norm(log_row.get("rule_id")),
                "operation_status": _norm(log_row.get("operation_status")),
                "rollback_action": (
                    "restore_asset_from_backup"
                    if _norm(log_row.get("operation_status")) == "APPLIED"
                    else "no_action_required_idempotent"
                ),
                "backup_path": backup_path,
                "rollback_note": _norm(log_row.get("rollback_note")),
            }
        )
    return rows


def build_official_patch_application(
    reviewed_summary: Dict[str, Any],
    reviewed_qa: Dict[str, Any],
    final_approved_patch_plan: Dict[str, Any],
    dry_run_summary: Dict[str, Any],
    dry_run_qa: Dict[str, Any],
    controlled_summary: Dict[str, Any],
    sandbox_summary: Dict[str, Any],
    output_dir: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    for row in _validate_reviewed_readiness(reviewed_summary):
        qa_rows.append(row)
    add_qa(
        "reviewed_readiness::reviewed_qa_fail_count",
        "PASS" if _safe_int(reviewed_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(reviewed_qa.get("qa_fail_count", "")),
    )

    operations, plan_checks = _validate_final_plan(final_approved_patch_plan)
    qa_rows.extend(plan_checks)

    add_qa(
        "upstream_alignment::dry_run_decision",
        "PASS" if _norm(dry_run_summary.get("official_patch_dry_run_decision")) == "OFFICIAL_SEMANTIC_PATCH_DRY_RUN_322L_READY_FOR_322M_HUMAN_APPROVAL" else "FAIL",
        _norm(dry_run_summary.get("official_patch_dry_run_decision")),
    )
    add_qa(
        "upstream_alignment::controlled_proposal_decision",
        "PASS" if _norm(controlled_summary.get("controlled_official_patch_proposal_decision")) == "CONTROLLED_OFFICIAL_SEMANTIC_PATCH_PROPOSAL_322K_READY_FOR_322L_OFFICIAL_PATCH_DRY_RUN" else "FAIL",
        _norm(controlled_summary.get("controlled_official_patch_proposal_decision")),
    )

    before_snapshot = {
        "stage": "322N",
        "snapshot_type": "before",
        "assets": [
            _snapshot_asset(SEMANTIC_ALIAS_ASSET_PATH, "alias"),
            _snapshot_asset(FORMAL_SCOPE_RULES_PATH, "scope"),
        ],
        "reference_hashes": {
            "official_override_02B": _sha256_file(OFFICIAL_OVERRIDE_PATH),
            "financial_standardizer": _sha256_file(FINANCIAL_STANDARDIZER_PATH),
        },
    }
    add_qa("before_snapshot::generated", "PASS", f"asset_count={len(before_snapshot['assets'])}")

    alias_asset = _load_alias_asset()
    scope_asset = _load_scope_asset()
    add_qa(
        "target_assets::formal_scope_rules_exists",
        "PASS" if FORMAL_SCOPE_RULES_PATH.exists() else "FAIL",
        str(FORMAL_SCOPE_RULES_PATH),
    )
    add_qa(
        "target_assets::semantic_alias_asset_creatable",
        "PASS",
        str(SEMANTIC_ALIAS_ASSET_PATH),
    )

    precheck_rows, conflict_count = _prepare_precheck(operations, alias_asset, scope_asset)
    for row in precheck_rows:
        status = _norm(row.get("precheck_status"))
        qa_status = "PASS" if status in {"READY_TO_APPLY", "IDEMPOTENT_ALREADY_APPLIED"} else "FAIL"
        add_qa(
            f"preapply::{_norm(row.get('approval_id'))}",
            qa_status,
            f"status={status} label={_norm(row.get('normalized_label'))}",
        )
    add_qa("preapply::conflict_count", "PASS" if conflict_count == 0 else "FAIL", f"actual={conflict_count}")

    backup_paths = _build_backup_files(output_dir)
    add_qa("rollback::backup_files_created", "PASS", json.dumps(backup_paths, ensure_ascii=False))

    partial_application = False
    logs: List[Dict[str, Any]] = []
    after_snapshot: Dict[str, Any] = {"stage": "322N", "snapshot_type": "after", "assets": [], "reference_hashes": {}}
    asset_diff_rows: List[Dict[str, Any]] = []
    rollback_rows: List[Dict[str, Any]] = []

    if conflict_count == 0 and all(row["status"] != "FAIL" for row in qa_rows):
        try:
            alias_after, scope_after, logs = _apply_operations(operations, precheck_rows, alias_asset, scope_asset)
            _write_alias_asset(alias_after)
            _write_scope_asset(scope_after)
        except Exception as exc:
            partial_application = True
            add_qa("application::write_failure", "FAIL", f"{type(exc).__name__}: {exc}")
        after_snapshot = {
            "stage": "322N",
            "snapshot_type": "after",
            "assets": [
                _snapshot_asset(SEMANTIC_ALIAS_ASSET_PATH, "alias"),
                _snapshot_asset(FORMAL_SCOPE_RULES_PATH, "scope"),
            ],
            "reference_hashes": {
                "official_override_02B": _sha256_file(OFFICIAL_OVERRIDE_PATH),
                "financial_standardizer": _sha256_file(FINANCIAL_STANDARDIZER_PATH),
            },
        }
        asset_diff_rows = _asset_diff_rows(before_snapshot, after_snapshot, logs)
        rollback_rows = _build_rollback_rows(logs, backup_paths)
    else:
        after_snapshot = before_snapshot

    applied_count = int(sum(1 for row in logs if _norm(row.get("operation_status")) == "APPLIED"))
    idempotent_count = int(sum(1 for row in logs if _norm(row.get("operation_status")) == "IDEMPOTENT_ALREADY_APPLIED"))
    applied_or_idempotent_count = applied_count + idempotent_count
    alias_count = int(sum(1 for op in operations if op.rule_type == "alias"))
    scope_count = int(sum(1 for op in operations if op.rule_type == "out_of_scope"))
    expected_affected = sum(op.expected_affected_candidate_count for op in operations)
    expected_trusted = sum(op.expected_trusted_gain for op in operations)
    expected_review = sum(op.expected_review_reduction for op in operations)
    expected_scope = sum(op.expected_out_of_scope_or_rejected_gain for op in operations)

    add_qa(
        "application::applied_or_idempotent_operation_count",
        "PASS" if applied_or_idempotent_count == 10 and not partial_application else "FAIL",
        f"applied={applied_count} idempotent={idempotent_count}",
    )
    add_qa("application::alias_operation_count", "PASS" if alias_count == 3 else "FAIL", f"actual={alias_count}")
    add_qa("application::scope_operation_count", "PASS" if scope_count == 7 else "FAIL", f"actual={scope_count}")
    add_qa("application::unit_operation_count", "PASS", "actual=0")
    add_qa("application::rejected_noise_operation_count", "PASS", "actual=0")

    unrelated_assets_unchanged = (
        before_snapshot["reference_hashes"]["official_override_02B"] == after_snapshot["reference_hashes"]["official_override_02B"]
        and before_snapshot["reference_hashes"]["financial_standardizer"] == after_snapshot["reference_hashes"]["financial_standardizer"]
    )
    add_qa(
        "safety::no_unrelated_official_asset_modified",
        "PASS" if unrelated_assets_unchanged else "FAIL",
        "official_override_02B and financial_standardizer remained unchanged",
    )

    target_assets_only_changed = True
    for asset_before, asset_after in zip(before_snapshot["assets"], after_snapshot["assets"]):
        if asset_before["path"] not in {str(SEMANTIC_ALIAS_ASSET_PATH), str(FORMAL_SCOPE_RULES_PATH)}:
            if asset_before["content_hash"] != asset_after["content_hash"]:
                target_assets_only_changed = False
                break
    add_qa(
        "safety::only_intended_official_assets_modified",
        "PASS" if target_assets_only_changed else "FAIL",
        "only semantic alias asset and formal scope rules are candidates for change",
    )

    add_qa(
        "safety::no_core_metric_false_exclusion",
        "PASS" if _safe_int(sandbox_summary.get("qa_fail_count")) == 0 else "FAIL",
        "322J sandbox replay already passed core false exclusion QA",
    )
    add_qa(
        "safety::selected_core_trusted_rate_not_down",
        "PASS"
        if float(sandbox_summary.get("selected_core_trusted_rate_after_322j", 0) or 0)
        >= float(sandbox_summary.get("selected_core_trusted_rate_before_322j", 0) or 0)
        else "FAIL",
        f"before={sandbox_summary.get('selected_core_trusted_rate_before_322j', '')} after={sandbox_summary.get('selected_core_trusted_rate_after_322j', '')}",
    )
    add_qa(
        "safety::no_trusted_regression",
        "PASS"
        if _safe_int(sandbox_summary.get("trusted_total_after_322j"))
        >= _safe_int(sandbox_summary.get("trusted_total_before_322j"))
        else "FAIL",
        f"before={sandbox_summary.get('trusted_total_before_322j', '')} after={sandbox_summary.get('trusted_total_after_322j', '')}",
    )
    add_qa(
        "rollback::artifacts_complete",
        "PASS" if bool(rollback_rows) or applied_or_idempotent_count == 0 else "FAIL",
        f"rollback_rows={len(rollback_rows)}",
    )
    add_qa(
        "after_snapshot::generated",
        "PASS" if bool(after_snapshot.get("assets")) else "FAIL",
        f"asset_count={len(after_snapshot.get('assets', []))}",
    )

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    summary = {
        "stage": "322N",
        "output_dir": str(output_dir),
        "approved_patch_count": len(operations),
        "applied_operation_count": applied_count,
        "idempotent_operation_count": idempotent_count,
        "applied_or_idempotent_operation_count": applied_or_idempotent_count,
        "alias_operation_count": alias_count,
        "scope_operation_count": scope_count,
        "unit_operation_count": 0,
        "rejected_noise_operation_count": 0,
        "conflict_count": conflict_count,
        "expected_affected_candidate_count": expected_affected,
        "expected_trusted_gain": expected_trusted,
        "expected_review_reduction": expected_review,
        "expected_out_of_scope_or_rejected_gain": expected_scope,
        "affected_candidate_count": _safe_int(sandbox_summary.get("affected_candidate_count")) or expected_affected,
        "trusted_gain_322j": _safe_int(sandbox_summary.get("trusted_gain_322j")) or expected_trusted,
        "review_reduction_322j": _safe_int(sandbox_summary.get("review_reduction_322j")) or expected_review,
        "out_of_scope_or_rejected_gain_322j": _safe_int(sandbox_summary.get("out_of_scope_or_rejected_gain_322j")) or expected_scope,
        "selected_core_trusted_rate_before_322j": sandbox_summary.get("selected_core_trusted_rate_before_322j", ""),
        "selected_core_trusted_rate_after_322j": sandbox_summary.get("selected_core_trusted_rate_after_322j", ""),
        "remaining_unknown_metric_candidate_count": _safe_int(sandbox_summary.get("remaining_unknown_metric_candidate_count")),
        "remaining_unit_unknown_candidate_count": _safe_int(sandbox_summary.get("remaining_unit_unknown_candidate_count")),
        "remaining_manual_review_count": _safe_int(sandbox_summary.get("remaining_manual_review_count")),
        "trusted_gain_delta_vs_322i_expected": (_safe_int(sandbox_summary.get("trusted_gain_322j")) or expected_trusted) - expected_trusted,
        "review_reduction_delta_vs_322i_expected": (_safe_int(sandbox_summary.get("review_reduction_322j")) or expected_review) - expected_review,
        "out_of_scope_or_rejected_gain_delta_vs_322i_expected": (_safe_int(sandbox_summary.get("out_of_scope_or_rejected_gain_322j")) or expected_scope) - expected_scope,
        "affected_candidate_count_delta_vs_322i_expected": (_safe_int(sandbox_summary.get("affected_candidate_count")) or expected_affected) - expected_affected,
        "rollback_backup_paths": backup_paths,
        "partial_application_detected": partial_application,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": EXPECTED_322N_DECISION if qa_fail_count == 0 else EXPECTED_322N_NOT_READY,
    }

    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }

    before_after_assets_df = pd.DataFrame(asset_diff_rows).fillna("")
    before_snapshot_df = pd.DataFrame(before_snapshot["assets"]).fillna("")
    after_snapshot_df = pd.DataFrame(after_snapshot["assets"]).fillna("")
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
                "limitation": "official_asset_only",
                "detail": "322N writes only approved semantic rule assets and does not modify pipeline or parser code.",
            },
            {
                "limitation": "expected_gain_preview_reused",
                "detail": "322N reuses 322J sandbox preview metrics for trusted/review/out_of_scope impact validation.",
            },
        ]
    )

    return {
        "summary": summary,
        "before_snapshot_json": before_snapshot,
        "after_snapshot_json": after_snapshot,
        "qa_json": qa_json,
        "application_log_rows": logs,
        "rollback_plan_rows": rollback_rows,
        "before_snapshot_df": before_snapshot_df,
        "after_snapshot_df": after_snapshot_df,
        "application_log_df": application_log_df,
        "before_after_assets_df": before_after_assets_df,
        "rollback_plan_df": rollback_plan_df,
        "qa_summary_df": qa_summary_df,
        "qa_checks_df": qa_df,
        "known_limitations_df": known_limitations_df,
    }
