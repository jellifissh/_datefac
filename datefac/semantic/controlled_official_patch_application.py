from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import pandas as pd


EXPECTED_323LR_DECISION = (
    "CONTROLLED_OFFICIAL_PROPOSAL_HUMAN_APPROVAL_323L_REVIEWED_READY_FOR_323M_OFFICIAL_PATCH_APPLICATION"
)
EXPECTED_323K_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_DRY_RUN_323K_READY_FOR_HUMAN_APPROVAL"
EXPECTED_323J_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_323J_READY_FOR_323K_DRY_RUN"
EXPECTED_323M_DECISION = "OFFICIAL_PATCH_APPLICATION_323M_READY_FOR_323N_POST_PATCH_REGRESSION"
EXPECTED_323M_NOT_READY = "OFFICIAL_PATCH_APPLICATION_323M_NOT_READY"

DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\official_patch_application_323m")
SEMANTIC_ALIAS_ASSET_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")
FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
ALIAS_TARGET_GROUP = "profitability"
SCOPE_TARGET_GROUP = "core_metric_scope_exclusions"

REFERENCE_FILE_PATHS = [
    Path(r"D:\_datefac\factory_core.py"),
    Path(r"D:\_datefac\financial_standardizer.py"),
]

EXPECTED_COUNTS = {
    "approved_patch_count": 6,
    "alias_operation_count": 2,
    "scope_operation_count": 4,
    "affected_candidate_count": 129,
    "expected_trusted_gain": 44,
    "expected_review_reduction": 129,
    "expected_out_of_scope_or_rejected_gain": 85,
}


@dataclass(frozen=True)
class ApprovedOperation:
    approval_id: str
    dry_run_patch_operation_id: str
    controlled_proposal_id: str
    source_rule_candidate_id: str
    candidate_type: str
    proposal_type: str
    future_operation_type: str
    target_asset_path: str
    target_group_name: str
    target_rule_family: str
    target_locator: str
    normalized_label: str
    metric_code: str
    metric_family: str
    scope_action: str
    generated_rule_id: str
    reviewer_decision: str
    reviewer_name: str
    reviewer_note: str
    approval_timestamp: str
    expected_affected_candidate_count: int
    expected_trusted_gain: int
    expected_review_reduction: int
    expected_out_of_scope_or_rejected_gain: int
    source_rule_ids: str
    source_confirmation_ids: str
    source_request_ids: str
    source_group_ids: str
    rollback_note: str
    risk_flags: str
    sample_table_titles: str
    sample_texts: str
    sample_years: str


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


def _canonical_reviewer_decision(value: Any) -> str:
    text = _norm(value).upper()
    if text == "APPROVE":
        return "APPROVED"
    if text == "REJECT":
        return "REJECTED"
    if text == "NEEDS_MORE_INFO":
        return "NEEDS_MORE_REVIEW"
    return text


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


def _read_json_as_df(path: Path, key: str) -> pd.DataFrame:
    payload = _read_json(path)
    rows = payload.get(key, [])
    if not isinstance(rows, list):
        rows = []
    return pd.DataFrame(rows).fillna("")


def _copy_text_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.exists():
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        dest.write_text(
            json.dumps({"file_exists": False, "path": str(src)}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _safe_numeric_sum(rows: Sequence[ApprovedOperation], attr: str) -> int:
    return int(sum(getattr(row, attr) for row in rows))


def _default_alias_asset() -> Dict[str, Any]:
    return {
        "schema_version": "1.0",
        "rule_family": "semantic_alias_candidates",
        "description": "Official semantic alias candidates approved for controlled semantic mapping.",
        "groups": {},
    }


def _load_alias_asset() -> Dict[str, Any]:
    payload = _read_json(SEMANTIC_ALIAS_ASSET_PATH)
    if not payload:
        return _default_alias_asset()
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
        "rule_family": payload.get("rule_family", "semantic_alias_candidates"),
        "description": payload.get(
            "description",
            "Official semantic alias candidates approved for controlled semantic mapping.",
        ),
        "groups": normalized_groups,
    }
    SEMANTIC_ALIAS_ASSET_PATH.write_text(
        json.dumps(_to_jsonable(output), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


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


def _snapshot_asset(path: Path, asset_type: str) -> Dict[str, Any]:
    if asset_type == "alias":
        payload = _load_alias_asset()
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


def _find_alias_matches(entries: Sequence[Dict[str, Any]], group_name: str, label: str) -> List[Dict[str, Any]]:
    label_key = _normalize_label(label)
    return [
        row
        for row in entries
        if _norm(row.get("target_group")) == _norm(group_name)
        and _normalize_label(row.get("normalized_label")) == label_key
    ]


def _find_scope_matches(entries: Sequence[Dict[str, Any]], group_name: str, label: str) -> List[Dict[str, Any]]:
    label_key = _normalize_label(label)
    return [
        row
        for row in entries
        if _norm(row.get("target_group")) == _norm(group_name)
        and _normalize_label(row.get("normalized_label")) == label_key
    ]


def _count_alias_duplicates(payload: Dict[str, Any]) -> int:
    seen: set[Tuple[str, str, str]] = set()
    duplicates = 0
    for row in _flatten_alias_entries(payload):
        key = (
            _norm(row.get("target_group")),
            _normalize_label(row.get("normalized_label")),
            _norm(row.get("metric_code")),
        )
        if key in seen:
            duplicates += 1
        else:
            seen.add(key)
    return duplicates


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


def _generated_rule_id(candidate_type: str, patch_operation_id: str) -> str:
    suffix = _norm(patch_operation_id).split("::")[-1] or "000"
    prefix = "SEM_ALIAS_323M_" if candidate_type == "alias" else "SEM_SCOPE_323M_"
    return f"{prefix}{suffix}"


def load_controlled_official_patch_application_inputs(
    reviewed_approval_dir: Path,
    dry_run_dir: Path,
    controlled_proposal_dir: Path,
) -> Dict[str, Any]:
    final_plan_path = (
        reviewed_approval_dir
        / "controlled_official_proposal_human_approval_323lr_final_approved_patch_plan.json"
    )
    patch_operations_path = (
        dry_run_dir / "controlled_official_proposal_dry_run_323k_patch_operations.json"
    )
    proposal_package_path = (
        controlled_proposal_dir
        / "controlled_official_proposal_from_323i_323j_proposal_package.json"
    )
    return {
        "reviewed_summary": _read_json(
            reviewed_approval_dir / "controlled_official_proposal_human_approval_323lr_summary.json"
        ),
        "reviewed_qa": _read_json(
            reviewed_approval_dir / "controlled_official_proposal_human_approval_323lr_qa.json"
        ),
        "final_approved_patch_plan": _read_json(final_plan_path),
        "dry_run_summary": _read_json(
            dry_run_dir / "controlled_official_proposal_dry_run_323k_summary.json"
        ),
        "dry_run_qa": _read_json(
            dry_run_dir / "controlled_official_proposal_dry_run_323k_qa.json"
        ),
        "patch_operations_df": _read_json_as_df(patch_operations_path, "patch_operations"),
        "controlled_summary": _read_json(
            controlled_proposal_dir / "controlled_official_proposal_from_323i_323j_summary.json"
        ),
        "controlled_qa": _read_json(
            controlled_proposal_dir / "controlled_official_proposal_from_323i_323j_qa.json"
        ),
        "controlled_proposals_df": _read_json_as_df(
            proposal_package_path, "controlled_proposals"
        ),
    }


def _validate_reviewed_readiness(summary: Dict[str, Any], qa: Dict[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add("readiness::323lr_decision", _norm(summary.get("decision")) == EXPECTED_323LR_DECISION, _norm(summary.get("decision")))
    add("readiness::323lr_summary_qa_fail_count", _safe_int(summary.get("qa_fail_count")) == 0, str(summary.get("qa_fail_count", "")))
    add("readiness::323lr_qa_json_fail_count", _safe_int(qa.get("qa_fail_count")) == 0, str(qa.get("qa_fail_count", "")))
    for key, expected in [
        ("approval_record_count", 6),
        ("approved_patch_operation_count", 6),
        ("alias_approved_patch_operation_count", 2),
        ("scope_approved_patch_operation_count", 4),
        ("rejected_count", 0),
        ("needs_more_info_count", 0),
        ("pending_count", 0),
        ("invalid_decision_count", 0),
    ]:
        add(
            f"readiness::323lr_{key}",
            _safe_int(summary.get(key)) == expected,
            f"expected={expected} actual={summary.get(key, '')}",
        )
    return checks


def _validate_dry_run_readiness(summary: Dict[str, Any], qa: Dict[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add("readiness::323k_decision", _norm(summary.get("decision")) == EXPECTED_323K_DECISION, _norm(summary.get("decision")))
    add("readiness::323k_summary_qa_fail_count", _safe_int(summary.get("qa_fail_count")) == 0, str(summary.get("qa_fail_count", "")))
    add("readiness::323k_qa_json_fail_count", _safe_int(qa.get("qa_fail_count")) == 0, str(qa.get("qa_fail_count", "")))
    for key, expected in [
        ("proposal_count", 6),
        ("alias_proposal_count", 2),
        ("scope_proposal_count", 4),
        ("patch_operation_count", 6),
        ("alias_patch_operation_count", 2),
        ("scope_patch_operation_count", 4),
        ("duplicate_operation_count", 0),
        ("target_conflict_count", 0),
        ("already_official_overlap_count", 0),
        ("affected_candidate_count", 129),
        ("expected_trusted_gain", 44),
        ("expected_review_reduction", 129),
        ("expected_out_of_scope_or_rejected_gain", 85),
    ]:
        add(
            f"readiness::323k_{key}",
            _safe_int(summary.get(key)) == expected,
            f"expected={expected} actual={summary.get(key, '')}",
        )
    return checks


def _validate_controlled_readiness(summary: Dict[str, Any], qa: Dict[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add("readiness::323j_decision", _norm(summary.get("decision")) == EXPECTED_323J_DECISION, _norm(summary.get("decision")))
    add("readiness::323j_summary_qa_fail_count", _safe_int(summary.get("qa_fail_count")) == 0, str(summary.get("qa_fail_count", "")))
    add("readiness::323j_qa_json_fail_count", _safe_int(qa.get("qa_fail_count")) == 0, str(qa.get("qa_fail_count", "")))
    for key, expected in [
        ("loaded_ready_candidate_count", 6),
        ("proposal_count", 6),
        ("alias_proposal_count", 2),
        ("scope_proposal_count", 4),
        ("target_conflict_count", 0),
        ("already_official_overlap_count", 0),
        ("expected_affected_candidate_count", 129),
        ("expected_trusted_gain", 44),
        ("expected_review_reduction", 129),
        ("expected_out_of_scope_or_rejected_gain", 85),
    ]:
        add(
            f"readiness::323j_{key}",
            _safe_int(summary.get(key)) == expected,
            f"expected={expected} actual={summary.get(key, '')}",
        )
    return checks


def _build_approved_operations(
    final_approved_patch_plan: Dict[str, Any],
    patch_operations_df: pd.DataFrame,
    controlled_proposals_df: pd.DataFrame,
) -> Tuple[List[ApprovedOperation], List[Dict[str, Any]]]:
    checks: List[Dict[str, Any]] = []
    approved_rows = final_approved_patch_plan.get("approved_patch_operations", [])
    approved_rows = approved_rows if isinstance(approved_rows, list) else []

    patch_lookup = {
        _norm(row.get("dry_run_patch_operation_id")): row
        for row in patch_operations_df.to_dict(orient="records")
    } if not patch_operations_df.empty else {}
    proposal_lookup = {
        _norm(row.get("controlled_proposal_id")): row
        for row in controlled_proposals_df.to_dict(orient="records")
    } if not controlled_proposals_df.empty else {}

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    operations: List[ApprovedOperation] = []
    missing_patch_count = 0
    missing_proposal_count = 0
    required_field_failures = 0

    for row in approved_rows:
        if not isinstance(row, dict):
            required_field_failures += 1
            continue
        approval_id = _norm(row.get("approval_id"))
        patch_operation_id = _norm(row.get("dry_run_patch_operation_id"))
        proposal_id = _norm(row.get("controlled_proposal_id"))
        patch_row = patch_lookup.get(patch_operation_id)
        proposal_row = proposal_lookup.get(proposal_id)
        if not patch_row:
            missing_patch_count += 1
            continue
        if not proposal_row:
            missing_proposal_count += 1
            continue

        candidate_type = _norm(row.get("candidate_type")) or _norm(proposal_row.get("candidate_type"))
        metric_code = _norm(proposal_row.get("proposed_metric_code"))
        metric_family = _norm(proposal_row.get("proposed_metric_family")) or ALIAS_TARGET_GROUP
        scope_action = _norm(proposal_row.get("proposed_scope_action")) or "exclude_from_core_metric_mapping"
        reviewer_decision = _canonical_reviewer_decision(row.get("reviewer_decision"))

        if not all(
            [
                approval_id,
                patch_operation_id,
                proposal_id,
                candidate_type,
                _norm(row.get("target_asset_path")),
                _norm(row.get("target_group_name")),
                _norm(row.get("normalized_label")),
                reviewer_decision == "APPROVED",
            ]
        ):
            required_field_failures += 1
            continue

        operations.append(
            ApprovedOperation(
                approval_id=approval_id,
                dry_run_patch_operation_id=patch_operation_id,
                controlled_proposal_id=proposal_id,
                source_rule_candidate_id=_norm(row.get("source_rule_candidate_id")) or _norm(proposal_row.get("source_rule_candidate_id")),
                candidate_type=candidate_type,
                proposal_type=_norm(row.get("proposal_type")) or _norm(proposal_row.get("proposal_type")),
                future_operation_type=_norm(row.get("future_operation_type")) or _norm(proposal_row.get("future_operation_type")),
                target_asset_path=_norm(row.get("target_asset_path")),
                target_group_name=_norm(row.get("target_group_name")),
                target_rule_family=_norm(row.get("target_rule_family")) or _norm(proposal_row.get("target_rule_family")),
                target_locator=_norm(row.get("target_locator")),
                normalized_label=_norm(row.get("normalized_label")),
                metric_code=metric_code,
                metric_family=metric_family,
                scope_action=scope_action,
                generated_rule_id=_generated_rule_id(candidate_type, patch_operation_id),
                reviewer_decision=reviewer_decision,
                reviewer_name=_norm(row.get("reviewer_name")),
                reviewer_note=_norm(row.get("reviewer_note")),
                approval_timestamp=_norm(row.get("approval_timestamp")),
                expected_affected_candidate_count=_safe_int(row.get("expected_affected_candidate_count")),
                expected_trusted_gain=_safe_int(row.get("expected_trusted_gain")),
                expected_review_reduction=_safe_int(row.get("expected_review_reduction")),
                expected_out_of_scope_or_rejected_gain=_safe_int(row.get("expected_out_of_scope_or_rejected_gain")),
                source_rule_ids=_norm(proposal_row.get("source_rule_ids")) or _norm(row.get("source_rule_ids")),
                source_confirmation_ids=_norm(proposal_row.get("source_confirmation_ids")) or _norm(row.get("source_confirmation_ids")),
                source_request_ids=_norm(proposal_row.get("source_request_ids")) or _norm(row.get("source_request_ids")),
                source_group_ids=_norm(proposal_row.get("source_group_ids")) or _norm(row.get("source_group_ids")),
                rollback_note=_norm(row.get("rollback_note")),
                risk_flags=_norm(patch_row.get("risk_flags")) or _norm(proposal_row.get("risk_flags")),
                sample_table_titles=_norm(patch_row.get("sample_table_titles")) or _norm(proposal_row.get("sample_table_titles")),
                sample_texts=_norm(patch_row.get("sample_texts")) or _norm(proposal_row.get("sample_texts")),
                sample_years=_norm(patch_row.get("sample_years")) or _norm(proposal_row.get("sample_years")),
            )
        )

    add("patch_plan::exists", bool(final_approved_patch_plan), "loaded" if final_approved_patch_plan else "missing_or_invalid")
    add("patch_plan::decision", _norm(final_approved_patch_plan.get("decision")) == EXPECTED_323LR_DECISION, _norm(final_approved_patch_plan.get("decision")))
    add("patch_plan::approved_patch_operation_count", len(operations) == 6, f"actual={len(operations)}")
    add(
        "patch_plan::no_rejected_patch_operations",
        len(final_approved_patch_plan.get("rejected_patch_operations", []) if isinstance(final_approved_patch_plan.get("rejected_patch_operations", []), list) else []) == 0,
        f"actual={len(final_approved_patch_plan.get('rejected_patch_operations', [])) if isinstance(final_approved_patch_plan.get('rejected_patch_operations', []), list) else 0}",
    )
    add(
        "patch_plan::no_needs_more_info_patch_operations",
        len(final_approved_patch_plan.get("needs_more_info_patch_operations", []) if isinstance(final_approved_patch_plan.get("needs_more_info_patch_operations", []), list) else []) == 0,
        f"actual={len(final_approved_patch_plan.get('needs_more_info_patch_operations', [])) if isinstance(final_approved_patch_plan.get('needs_more_info_patch_operations', []), list) else 0}",
    )
    add("patch_plan::all_patch_operations_found_in_323k", missing_patch_count == 0, f"missing={missing_patch_count}")
    add("patch_plan::all_proposals_found_in_323j", missing_proposal_count == 0, f"missing={missing_proposal_count}")
    add("patch_plan::required_fields_complete", required_field_failures == 0, f"failed_records={required_field_failures}")
    add(
        "patch_plan::no_duplicate_approval_id",
        len({op.approval_id for op in operations}) == len(operations),
        f"actual={len(operations)} unique={len({op.approval_id for op in operations})}",
    )
    add(
        "patch_plan::no_duplicate_patch_operation_id",
        len({op.dry_run_patch_operation_id for op in operations}) == len(operations),
        f"actual={len(operations)} unique={len({op.dry_run_patch_operation_id for op in operations})}",
    )
    alias_count = int(sum(1 for op in operations if op.candidate_type == "alias"))
    scope_count = int(sum(1 for op in operations if op.candidate_type == "scope"))
    add("patch_plan::alias_operation_count", alias_count == 2, f"actual={alias_count}")
    add("patch_plan::scope_operation_count", scope_count == 4, f"actual={scope_count}")
    add(
        "patch_plan::affected_candidate_count",
        _safe_numeric_sum(operations, "expected_affected_candidate_count") == 129,
        f"actual={_safe_numeric_sum(operations, 'expected_affected_candidate_count')}",
    )
    add(
        "patch_plan::expected_trusted_gain",
        _safe_numeric_sum(operations, "expected_trusted_gain") == 44,
        f"actual={_safe_numeric_sum(operations, 'expected_trusted_gain')}",
    )
    add(
        "patch_plan::expected_review_reduction",
        _safe_numeric_sum(operations, "expected_review_reduction") == 129,
        f"actual={_safe_numeric_sum(operations, 'expected_review_reduction')}",
    )
    add(
        "patch_plan::expected_out_of_scope_or_rejected_gain",
        _safe_numeric_sum(operations, "expected_out_of_scope_or_rejected_gain") == 85,
        f"actual={_safe_numeric_sum(operations, 'expected_out_of_scope_or_rejected_gain')}",
    )
    return operations, checks


def _prepare_precheck(
    operations: Sequence[ApprovedOperation],
    alias_payload: Dict[str, Any],
    scope_payload: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], int]:
    alias_entries = _flatten_alias_entries(alias_payload)
    scope_entries = _flatten_scope_entries(scope_payload)
    rows: List[Dict[str, Any]] = []
    conflict_count = 0

    for op in operations:
        if op.candidate_type == "alias":
            matches = _find_alias_matches(alias_entries, op.target_group_name, op.normalized_label)
            exact_match = next(
                (
                    item
                    for item in matches
                    if _norm(item.get("metric_code")) == op.metric_code
                ),
                None,
            )
            conflicting_match = next(
                (
                    item
                    for item in matches
                    if _norm(item.get("metric_code")) != op.metric_code
                ),
                None,
            )
            generated_rule_conflict = next(
                (
                    item
                    for item in alias_entries
                    if _norm(item.get("rule_id")) == op.generated_rule_id
                    and (
                        _normalize_label(item.get("normalized_label")) != _normalize_label(op.normalized_label)
                        or _norm(item.get("metric_code")) != op.metric_code
                    )
                ),
                None,
            )
            group_before_count = int(
                sum(1 for item in alias_entries if _norm(item.get("target_group")) == op.target_group_name)
            )
            if exact_match:
                status = "IDEMPOTENT_ALREADY_APPLIED"
                before_state = exact_match
            elif conflicting_match or generated_rule_conflict:
                status = "CONFLICT"
                before_state = conflicting_match or generated_rule_conflict
                conflict_count += 1
            elif op.target_asset_path != str(SEMANTIC_ALIAS_ASSET_PATH) or op.target_group_name != ALIAS_TARGET_GROUP:
                status = "CONFLICT"
                before_state = {}
                conflict_count += 1
            else:
                status = "READY_TO_APPLY"
                before_state = {}

            rows.append(
                {
                    "approval_id": op.approval_id,
                    "dry_run_patch_operation_id": op.dry_run_patch_operation_id,
                    "candidate_type": op.candidate_type,
                    "normalized_label": op.normalized_label,
                    "target_group_name": op.target_group_name,
                    "target_asset_path": op.target_asset_path,
                    "generated_rule_id": op.generated_rule_id,
                    "group_before_entry_count": group_before_count,
                    "group_after_entry_count_preview": group_before_count + (0 if status == "IDEMPOTENT_ALREADY_APPLIED" else 1),
                    "precheck_status": status,
                    "before_state": before_state,
                }
            )
            continue

        matches = _find_scope_matches(scope_entries, op.target_group_name, op.normalized_label)
        exact_match = next(
            (
                item
                for item in matches
                if _norm(item.get("scope_action")) == op.scope_action
            ),
            None,
        )
        conflicting_match = next(
            (
                item
                for item in matches
                if _norm(item.get("scope_action")) != op.scope_action
            ),
            None,
        )
        generated_rule_conflict = next(
            (
                item
                for item in scope_entries
                if _norm(item.get("rule_id")) == op.generated_rule_id
                and (
                    _normalize_label(item.get("normalized_label")) != _normalize_label(op.normalized_label)
                    or _norm(item.get("scope_action")) != op.scope_action
                )
            ),
            None,
        )
        group_before_count = int(
            sum(1 for item in scope_entries if _norm(item.get("target_group")) == op.target_group_name)
        )
        if exact_match:
            status = "IDEMPOTENT_ALREADY_APPLIED"
            before_state = exact_match
        elif conflicting_match or generated_rule_conflict:
            status = "CONFLICT"
            before_state = conflicting_match or generated_rule_conflict
            conflict_count += 1
        elif op.target_asset_path != str(FORMAL_SCOPE_RULES_PATH) or op.target_group_name != SCOPE_TARGET_GROUP:
            status = "CONFLICT"
            before_state = {}
            conflict_count += 1
        else:
            status = "READY_TO_APPLY"
            before_state = {}

        rows.append(
            {
                "approval_id": op.approval_id,
                "dry_run_patch_operation_id": op.dry_run_patch_operation_id,
                "candidate_type": op.candidate_type,
                "normalized_label": op.normalized_label,
                "target_group_name": op.target_group_name,
                "target_asset_path": op.target_asset_path,
                "generated_rule_id": op.generated_rule_id,
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
    alias_payload: Dict[str, Any],
    scope_payload: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
    alias_mutable = deepcopy(alias_payload)
    scope_mutable = deepcopy(scope_payload)
    alias_groups = alias_mutable.setdefault("groups", {})
    if not isinstance(alias_groups, dict):
        alias_groups = {}
        alias_mutable["groups"] = alias_groups
    alias_groups.setdefault(ALIAS_TARGET_GROUP, [])
    if not isinstance(alias_groups[ALIAS_TARGET_GROUP], list):
        alias_groups[ALIAS_TARGET_GROUP] = []

    scope_rules = scope_mutable.setdefault("rules", {})
    if not isinstance(scope_rules, dict):
        scope_rules = {}
        scope_mutable["rules"] = scope_rules

    precheck_lookup = {_norm(row.get("approval_id")): row for row in precheck_rows}
    logs: List[Dict[str, Any]] = []

    for op in operations:
        precheck = precheck_lookup.get(op.approval_id, {})
        status = _norm(precheck.get("precheck_status"))
        before_state = precheck.get("before_state") or {}
        after_state: Dict[str, Any] | None = None

        if op.candidate_type == "alias":
            if status == "READY_TO_APPLY":
                new_entry = {
                    "rule_id": op.generated_rule_id,
                    "normalized_label": op.normalized_label,
                    "metric_code": op.metric_code,
                    "metric_family": op.metric_family,
                    "source_approval_id": op.approval_id,
                    "source_dry_run_patch_operation_id": op.dry_run_patch_operation_id,
                    "source_controlled_proposal_id": op.controlled_proposal_id,
                    "source_rule_candidate_id": op.source_rule_candidate_id,
                    "source_rule_ids": op.source_rule_ids,
                    "source_confirmation_ids": op.source_confirmation_ids,
                    "source_request_ids": op.source_request_ids,
                    "source_group_ids": op.source_group_ids,
                    "reviewer_name": op.reviewer_name,
                    "reviewer_note": op.reviewer_note,
                    "approval_timestamp": op.approval_timestamp,
                    "approval_stage": "323M",
                    "status": "APPLIED_323M",
                }
                alias_groups[ALIAS_TARGET_GROUP].append(new_entry)
                after_state = new_entry
                status = "APPLIED"
            elif status == "IDEMPOTENT_ALREADY_APPLIED":
                after_state = before_state

        else:
            if status == "READY_TO_APPLY":
                new_rule = {
                    "rule_id": op.generated_rule_id,
                    "rule_type": "core_metric_scope_exclusion",
                    "target_group": op.target_group_name,
                    "normalized_label": op.normalized_label,
                    "scope_action": op.scope_action,
                    "existing_scope": op.scope_action,
                    "scope_applicability": [
                        "GLOBAL_ALIAS_MATCH_ONLY",
                        "EXCLUDE_FROM_CORE_METRIC_MAPPING",
                    ],
                    "source_approval_id": op.approval_id,
                    "source_dry_run_patch_operation_id": op.dry_run_patch_operation_id,
                    "source_controlled_proposal_id": op.controlled_proposal_id,
                    "source_rule_candidate_id": op.source_rule_candidate_id,
                    "source_rule_ids": op.source_rule_ids,
                    "source_confirmation_ids": op.source_confirmation_ids,
                    "source_request_ids": op.source_request_ids,
                    "source_group_ids": op.source_group_ids,
                    "reviewer_name": op.reviewer_name,
                    "reviewer_note": op.reviewer_note,
                    "approval_timestamp": op.approval_timestamp,
                    "promotion_status": "PROMOTED_323M_OFFICIAL_PATCH",
                }
                scope_rules[op.generated_rule_id] = new_rule
                after_state = new_rule
                status = "APPLIED"
            elif status == "IDEMPOTENT_ALREADY_APPLIED":
                after_state = before_state

        logs.append(
            {
                "approval_id": op.approval_id,
                "dry_run_patch_operation_id": op.dry_run_patch_operation_id,
                "controlled_proposal_id": op.controlled_proposal_id,
                "candidate_type": op.candidate_type,
                "proposal_type": op.proposal_type,
                "operation_status": status,
                "target_asset_path": op.target_asset_path,
                "target_group_name": op.target_group_name,
                "generated_rule_id": op.generated_rule_id,
                "normalized_label": op.normalized_label,
                "metric_code": op.metric_code,
                "scope_action": op.scope_action,
                "before_state": before_state,
                "after_state": after_state,
                "expected_affected_candidate_count": op.expected_affected_candidate_count,
                "expected_trusted_gain": op.expected_trusted_gain,
                "expected_review_reduction": op.expected_review_reduction,
                "expected_out_of_scope_or_rejected_gain": op.expected_out_of_scope_or_rejected_gain,
                "source_rule_candidate_id": op.source_rule_candidate_id,
                "source_rule_ids": op.source_rule_ids,
                "source_confirmation_ids": op.source_confirmation_ids,
                "source_request_ids": op.source_request_ids,
                "source_group_ids": op.source_group_ids,
                "rollback_note": op.rollback_note,
                "risk_flags": op.risk_flags,
                "sample_table_titles": op.sample_table_titles,
                "sample_texts": op.sample_texts,
                "sample_years": op.sample_years,
            }
        )

    return alias_mutable, scope_mutable, logs


def _asset_diff_rows(
    before_snapshot: Dict[str, Any],
    after_snapshot: Dict[str, Any],
    logs: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
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
    for row in logs:
        rows.append(
            {
                "target_path": row.get("target_asset_path", ""),
                "operation_status": row.get("operation_status", ""),
                "candidate_type": row.get("candidate_type", ""),
                "target_group_name": row.get("target_group_name", ""),
                "generated_rule_id": row.get("generated_rule_id", ""),
                "normalized_label": row.get("normalized_label", ""),
                "before_state": json.dumps(_to_jsonable(row.get("before_state")), ensure_ascii=False),
                "after_state": json.dumps(_to_jsonable(row.get("after_state")), ensure_ascii=False),
                "rollback_note": row.get("rollback_note", ""),
            }
        )
    return rows


def _build_backup_files(output_dir: Path) -> Dict[str, str]:
    backup_dir = output_dir / "rollback_backups"
    alias_backup = backup_dir / "semantic_alias_candidates.before_323m.json"
    scope_backup = backup_dir / "formal_scope_rules.before_323m.json"
    _copy_text_file(SEMANTIC_ALIAS_ASSET_PATH, alias_backup)
    _copy_text_file(FORMAL_SCOPE_RULES_PATH, scope_backup)
    return {
        "alias_backup_path": str(alias_backup),
        "scope_backup_path": str(scope_backup),
    }


def _build_rollback_rows(logs: Sequence[Dict[str, Any]], backup_paths: Dict[str, str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in logs:
        target_path = _norm(row.get("target_asset_path"))
        backup_path = (
            backup_paths["alias_backup_path"]
            if target_path == str(SEMANTIC_ALIAS_ASSET_PATH)
            else backup_paths["scope_backup_path"]
        )
        status = _norm(row.get("operation_status"))
        rows.append(
            {
                "approval_id": _norm(row.get("approval_id")),
                "dry_run_patch_operation_id": _norm(row.get("dry_run_patch_operation_id")),
                "candidate_type": _norm(row.get("candidate_type")),
                "generated_rule_id": _norm(row.get("generated_rule_id")),
                "target_path": target_path,
                "operation_status": status,
                "rollback_action": (
                    "restore_asset_from_backup"
                    if status == "APPLIED"
                    else "no_action_required_idempotent"
                ),
                "backup_path": backup_path,
                "rollback_note": _norm(row.get("rollback_note")),
            }
        )
    return rows


def build_controlled_official_patch_application(
    reviewed_summary: Dict[str, Any],
    reviewed_qa: Dict[str, Any],
    final_approved_patch_plan: Dict[str, Any],
    dry_run_summary: Dict[str, Any],
    dry_run_qa: Dict[str, Any],
    patch_operations_df: pd.DataFrame,
    controlled_summary: Dict[str, Any],
    controlled_qa: Dict[str, Any],
    controlled_proposals_df: pd.DataFrame,
    output_dir: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    for row in _validate_reviewed_readiness(reviewed_summary, reviewed_qa):
        qa_rows.append(row)
    for row in _validate_dry_run_readiness(dry_run_summary, dry_run_qa):
        qa_rows.append(row)
    for row in _validate_controlled_readiness(controlled_summary, controlled_qa):
        qa_rows.append(row)

    operations, plan_checks = _build_approved_operations(
        final_approved_patch_plan=final_approved_patch_plan,
        patch_operations_df=patch_operations_df,
        controlled_proposals_df=controlled_proposals_df,
    )
    qa_rows.extend(plan_checks)

    add_qa(
        "targets::only_expected_official_alias_asset",
        "PASS"
        if all(
            op.target_asset_path == str(SEMANTIC_ALIAS_ASSET_PATH)
            for op in operations
            if op.candidate_type == "alias"
        )
        else "FAIL",
        str(SEMANTIC_ALIAS_ASSET_PATH),
    )
    add_qa(
        "targets::only_expected_scope_asset",
        "PASS"
        if all(
            op.target_asset_path == str(FORMAL_SCOPE_RULES_PATH)
            for op in operations
            if op.candidate_type == "scope"
        )
        else "FAIL",
        str(FORMAL_SCOPE_RULES_PATH),
    )
    add_qa(
        "targets::alias_group_is_profitability",
        "PASS"
        if all(
            op.target_group_name == ALIAS_TARGET_GROUP
            for op in operations
            if op.candidate_type == "alias"
        )
        else "FAIL",
        ALIAS_TARGET_GROUP,
    )
    add_qa(
        "targets::scope_group_is_core_metric_scope_exclusions",
        "PASS"
        if all(
            op.target_group_name == SCOPE_TARGET_GROUP
            for op in operations
            if op.candidate_type == "scope"
        )
        else "FAIL",
        SCOPE_TARGET_GROUP,
    )

    reference_hashes_before = {str(path): _sha256_file(path) for path in REFERENCE_FILE_PATHS}
    before_snapshot = {
        "stage": "323M",
        "snapshot_type": "before",
        "assets": [
            _snapshot_asset(SEMANTIC_ALIAS_ASSET_PATH, "alias"),
            _snapshot_asset(FORMAL_SCOPE_RULES_PATH, "scope"),
        ],
        "reference_hashes": reference_hashes_before,
    }
    add_qa("before_snapshot::generated", "PASS", f"asset_count={len(before_snapshot['assets'])}")

    alias_payload = _load_alias_asset()
    scope_payload = _load_scope_asset()
    add_qa("target_assets::alias_asset_readable", "PASS" if isinstance(alias_payload.get("groups"), dict) else "FAIL", str(SEMANTIC_ALIAS_ASSET_PATH))
    add_qa("target_assets::scope_asset_readable", "PASS" if isinstance(scope_payload.get("rules"), dict) else "FAIL", str(FORMAL_SCOPE_RULES_PATH))

    precheck_rows, conflict_count = _prepare_precheck(operations, alias_payload, scope_payload)
    for row in precheck_rows:
        status = _norm(row.get("precheck_status"))
        add_qa(
            f"preapply::{_norm(row.get('approval_id'))}",
            "PASS" if status in {"READY_TO_APPLY", "IDEMPOTENT_ALREADY_APPLIED"} else "FAIL",
            f"status={status} label={_norm(row.get('normalized_label'))}",
        )
    add_qa("preapply::conflict_count", "PASS" if conflict_count == 0 else "FAIL", f"actual={conflict_count}")

    backup_paths = _build_backup_files(output_dir)
    add_qa("rollback::backup_files_created", "PASS", json.dumps(backup_paths, ensure_ascii=False))

    apply_blocked = any(row["status"] == "FAIL" for row in qa_rows) or conflict_count > 0
    partial_application_detected = False
    logs: List[Dict[str, Any]] = []

    if not apply_blocked:
        alias_after_payload, scope_after_payload, logs = _apply_operations(
            operations=operations,
            precheck_rows=precheck_rows,
            alias_payload=alias_payload,
            scope_payload=scope_payload,
        )
        try:
            _write_alias_asset(alias_after_payload)
            _write_scope_asset(scope_after_payload)
        except Exception as exc:
            partial_application_detected = True
            add_qa("application::write_failure", "FAIL", f"{type(exc).__name__}: {exc}")
    else:
        alias_after_payload = alias_payload
        scope_after_payload = scope_payload

    after_snapshot = {
        "stage": "323M",
        "snapshot_type": "after",
        "assets": [
            _snapshot_asset(SEMANTIC_ALIAS_ASSET_PATH, "alias"),
            _snapshot_asset(FORMAL_SCOPE_RULES_PATH, "scope"),
        ],
        "reference_hashes": {str(path): _sha256_file(path) for path in REFERENCE_FILE_PATHS},
    }
    add_qa("after_snapshot::generated", "PASS", f"asset_count={len(after_snapshot['assets'])}")

    modified_target_assets = [
        asset_after["path"]
        for asset_before, asset_after in zip(before_snapshot["assets"], after_snapshot["assets"])
        if asset_before.get("content_hash") != asset_after.get("content_hash")
    ]

    applied_count = int(sum(1 for row in logs if _norm(row.get("operation_status")) == "APPLIED"))
    idempotent_count = int(
        sum(1 for row in logs if _norm(row.get("operation_status")) == "IDEMPOTENT_ALREADY_APPLIED")
    )
    applied_or_idempotent_count = applied_count + idempotent_count
    alias_count = int(sum(1 for op in operations if op.candidate_type == "alias"))
    scope_count = int(sum(1 for op in operations if op.candidate_type == "scope"))

    add_qa(
        "application::approved_patch_count",
        "PASS" if len(operations) == 6 else "FAIL",
        f"actual={len(operations)}",
    )
    add_qa(
        "application::applied_or_idempotent_operation_count",
        "PASS" if applied_or_idempotent_count == 6 and not partial_application_detected else "FAIL",
        f"applied={applied_count} idempotent={idempotent_count}",
    )
    add_qa("application::alias_operation_count", "PASS" if alias_count == 2 else "FAIL", f"actual={alias_count}")
    add_qa("application::scope_operation_count", "PASS" if scope_count == 4 else "FAIL", f"actual={scope_count}")

    alias_duplicate_count_before = _count_alias_duplicates(alias_payload)
    scope_duplicate_count_before = _count_scope_duplicates(scope_payload)
    alias_duplicates = _count_alias_duplicates(_load_alias_asset())
    scope_duplicates = _count_scope_duplicates(_load_scope_asset())
    duplicate_entry_count = alias_duplicates + scope_duplicates
    duplicate_entry_count_before = alias_duplicate_count_before + scope_duplicate_count_before
    duplicate_entry_count_delta = duplicate_entry_count - duplicate_entry_count_before
    add_qa(
        "postapply::no_new_duplicate_entries",
        "PASS" if duplicate_entry_count_delta == 0 else "FAIL",
        f"before={duplicate_entry_count_before} after={duplicate_entry_count} delta={duplicate_entry_count_delta}",
    )

    rerun_precheck_rows, rerun_conflict_count = _prepare_precheck(
        operations=operations,
        alias_payload=_load_alias_asset(),
        scope_payload=_load_scope_asset(),
    )
    rerun_all_idempotent = all(
        _norm(row.get("precheck_status")) == "IDEMPOTENT_ALREADY_APPLIED"
        for row in rerun_precheck_rows
    ) if rerun_precheck_rows else False
    add_qa(
        "idempotency::rerun_would_be_idempotent",
        "PASS" if rerun_all_idempotent and rerun_conflict_count == 0 else "FAIL",
        f"rows={len(rerun_precheck_rows)} conflicts={rerun_conflict_count}",
    )

    reference_files_unchanged = all(
        reference_hashes_before.get(path) == after_snapshot["reference_hashes"].get(path)
        for path in reference_hashes_before
    )
    add_qa(
        "safety::reference_production_files_unchanged",
        "PASS" if reference_files_unchanged else "FAIL",
        "factory_core.py and financial_standardizer.py remained unchanged",
    )
    add_qa(
        "safety::only_intended_official_assets_modified",
        "PASS"
        if set(modified_target_assets).issubset({str(SEMANTIC_ALIAS_ASSET_PATH), str(FORMAL_SCOPE_RULES_PATH)})
        else "FAIL",
        json.dumps(modified_target_assets, ensure_ascii=False),
    )
    add_qa(
        "rollback::backup_files_present",
        "PASS"
        if all(Path(path).exists() for path in backup_paths.values())
        else "FAIL",
        json.dumps(backup_paths, ensure_ascii=False),
    )

    before_after_preview_rows = []
    before_by_path = {item["path"]: item for item in before_snapshot["assets"]}
    after_by_path = {item["path"]: item for item in after_snapshot["assets"]}
    for path, candidate_type, target_group_name in [
        (str(SEMANTIC_ALIAS_ASSET_PATH), "alias", ALIAS_TARGET_GROUP),
        (str(FORMAL_SCOPE_RULES_PATH), "scope", SCOPE_TARGET_GROUP),
    ]:
        before_item = before_by_path.get(path, {})
        after_item = after_by_path.get(path, {})
        before_after_preview_rows.append(
            {
                "target_asset_path": path,
                "target_group_name": target_group_name,
                "candidate_type": candidate_type,
                "before_entry_count": before_item.get("group_counts", {}).get(target_group_name, 0),
                "after_entry_count": after_item.get("group_counts", {}).get(target_group_name, 0),
                "added_operation_count": int(
                    sum(
                        1
                        for row in logs
                        if _norm(row.get("candidate_type")) == candidate_type
                        and _norm(row.get("operation_status")) == "APPLIED"
                    )
                ),
                "affected_candidate_count": int(
                    sum(
                        _safe_int(row.get("expected_affected_candidate_count"))
                        for row in logs
                        if _norm(row.get("candidate_type")) == candidate_type
                    )
                ),
                "expected_trusted_gain": int(
                    sum(
                        _safe_int(row.get("expected_trusted_gain"))
                        for row in logs
                        if _norm(row.get("candidate_type")) == candidate_type
                    )
                ),
                "expected_review_reduction": int(
                    sum(
                        _safe_int(row.get("expected_review_reduction"))
                        for row in logs
                        if _norm(row.get("candidate_type")) == candidate_type
                    )
                ),
                "expected_out_of_scope_or_rejected_gain": int(
                    sum(
                        _safe_int(row.get("expected_out_of_scope_or_rejected_gain"))
                        for row in logs
                        if _norm(row.get("candidate_type")) == candidate_type
                    )
                ),
            }
        )

    rollback_rows = _build_rollback_rows(logs, backup_paths)
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
        "stage": "323M",
        "output_dir": str(output_dir),
        "approved_patch_count": len(operations),
        "alias_approved_patch_count": alias_count,
        "scope_approved_patch_count": scope_count,
        "applied_operation_count": applied_count,
        "idempotent_operation_count": idempotent_count,
        "applied_or_idempotent_operation_count": applied_or_idempotent_count,
        "alias_operation_count": alias_count,
        "scope_operation_count": scope_count,
        "conflict_count": conflict_count + rerun_conflict_count,
        "duplicate_entry_count_before": duplicate_entry_count_before,
        "duplicate_entry_count": duplicate_entry_count,
        "duplicate_entry_count_delta": duplicate_entry_count_delta,
        "affected_candidate_count": _safe_numeric_sum(operations, "expected_affected_candidate_count"),
        "expected_affected_candidate_count": _safe_numeric_sum(operations, "expected_affected_candidate_count"),
        "expected_trusted_gain": _safe_numeric_sum(operations, "expected_trusted_gain"),
        "expected_review_reduction": _safe_numeric_sum(operations, "expected_review_reduction"),
        "expected_out_of_scope_or_rejected_gain": _safe_numeric_sum(
            operations, "expected_out_of_scope_or_rejected_gain"
        ),
        "target_assets_modified": modified_target_assets,
        "rollback_backup_paths": backup_paths,
        "partial_application_detected": partial_application_detected,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": EXPECTED_323M_DECISION if qa_fail_count == 0 else EXPECTED_323M_NOT_READY,
    }

    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }

    apply_proof_json = {
        "stage": "323M",
        "decision": summary["decision"],
        "files_read": [
            str(Path(r"D:\_datefac\output\controlled_official_proposal_human_approval_323lr\controlled_official_proposal_human_approval_323lr_summary.json")),
            str(Path(r"D:\_datefac\output\controlled_official_proposal_human_approval_323lr\controlled_official_proposal_human_approval_323lr_qa.json")),
            str(Path(r"D:\_datefac\output\controlled_official_proposal_human_approval_323lr\controlled_official_proposal_human_approval_323lr_final_approved_patch_plan.json")),
            str(Path(r"D:\_datefac\output\controlled_official_proposal_dry_run_323k\controlled_official_proposal_dry_run_323k_summary.json")),
            str(Path(r"D:\_datefac\output\controlled_official_proposal_dry_run_323k\controlled_official_proposal_dry_run_323k_qa.json")),
            str(Path(r"D:\_datefac\output\controlled_official_proposal_dry_run_323k\controlled_official_proposal_dry_run_323k_patch_operations.json")),
            str(Path(r"D:\_datefac\output\controlled_official_proposal_from_323i_323j\controlled_official_proposal_from_323i_323j_summary.json")),
            str(Path(r"D:\_datefac\output\controlled_official_proposal_from_323i_323j\controlled_official_proposal_from_323i_323j_qa.json")),
            str(Path(r"D:\_datefac\output\controlled_official_proposal_from_323i_323j\controlled_official_proposal_from_323i_323j_proposal_package.json")),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
        "official_assets_before": {
            item["path"]: item["content_hash"] for item in before_snapshot["assets"]
        },
        "official_assets_after": {
            item["path"]: item["content_hash"] for item in after_snapshot["assets"]
        },
        "official_assets_written": modified_target_assets,
        "reference_files_unchanged": reference_files_unchanged,
        "approved_patch_operation_ids": [op.dry_run_patch_operation_id for op in operations],
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
        "rollback_backups": backup_paths,
        "only_intended_assets_modified": set(modified_target_assets).issubset(
            {str(SEMANTIC_ALIAS_ASSET_PATH), str(FORMAL_SCOPE_RULES_PATH)}
        ),
    }

    before_snapshot_df = pd.DataFrame(before_snapshot["assets"]).fillna("")
    after_snapshot_df = pd.DataFrame(after_snapshot["assets"]).fillna("")
    before_after_assets_df = pd.DataFrame(asset_diff_rows).fillna("")
    application_log_df = pd.DataFrame(logs).fillna("")
    rollback_plan_df = pd.DataFrame(rollback_rows).fillna("")
    before_after_preview_df = pd.DataFrame(before_after_preview_rows).fillna("")
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
                "limitation": "official_assets_only",
                "detail": "323M writes only the two approved semantic official assets and does not modify production pipeline, parser, extraction, or delivery code.",
            },
            {
                "limitation": "carried_forward_impact",
                "detail": "323M carries forward impact metrics from the approved 323K/323L-R package and does not recalculate trusted totals from pipeline replay in this stage.",
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
        "before_after_assets_df": before_after_assets_df,
        "application_log_df": application_log_df,
        "rollback_plan_df": rollback_plan_df,
        "qa_summary_df": qa_summary_df,
        "qa_checks_df": qa_df,
        "known_limitations_df": known_limitations_df,
    }
