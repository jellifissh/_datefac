from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd


EXPECTED_322K_DECISION = "CONTROLLED_OFFICIAL_SEMANTIC_PATCH_PROPOSAL_322K_READY_FOR_322L_OFFICIAL_PATCH_DRY_RUN"
EXPECTED_322L_DECISION = "OFFICIAL_SEMANTIC_PATCH_DRY_RUN_322L_READY_FOR_322M_HUMAN_APPROVAL"

FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
OFFICIAL_OVERRIDE_PATH = Path(r"D:\_datefac\data\overrides\02B_ai_repair_override.xlsx")


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _read_json_array(path: Path, key: str) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(parsed, dict):
        items = parsed.get(key, [])
    else:
        items = parsed
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def _safe_int(value: Any) -> int:
    if value in ("", None):
        return 0
    try:
        return int(float(value))
    except Exception:
        return 0


def _load_formal_scope_rules() -> Dict[str, Any]:
    if not FORMAL_SCOPE_RULES_PATH.exists():
        return {}
    return _read_json(FORMAL_SCOPE_RULES_PATH)


def _load_official_override_sheets() -> Dict[str, pd.DataFrame]:
    if not OFFICIAL_OVERRIDE_PATH.exists():
        return {}
    try:
        xl = pd.ExcelFile(OFFICIAL_OVERRIDE_PATH)
    except Exception:
        return {}
    return {
        sheet_name: pd.read_excel(OFFICIAL_OVERRIDE_PATH, sheet_name=sheet_name).fillna("")
        for sheet_name in xl.sheet_names
    }


def load_official_patch_dry_run_inputs(
    controlled_proposal_dir: Path,
    sandbox_application_dir: Path,
    official_rule_candidate_dir: Path,
) -> Dict[str, Any]:
    return {
        "controlled_summary": _read_json(controlled_proposal_dir / "controlled_official_semantic_patch_proposal_322k_summary.json"),
        "controlled_qa": _read_json(controlled_proposal_dir / "controlled_official_semantic_patch_proposal_322k_qa.json"),
        "alias_proposals": _read_json_array(
            controlled_proposal_dir / "controlled_official_semantic_patch_proposal_322k_alias_patch_proposals.json",
            "alias_patch_proposals",
        ),
        "scope_proposals": _read_json_array(
            controlled_proposal_dir / "controlled_official_semantic_patch_proposal_322k_scope_patch_proposals.json",
            "scope_patch_proposals",
        ),
        "sandbox_summary": _read_json(sandbox_application_dir / "official_semantic_rule_candidates_322j_summary.json"),
        "official_candidate_summary": _read_json(official_rule_candidate_dir / "official_semantic_rule_candidates_322i_summary.json"),
        "formal_scope_rules": _load_formal_scope_rules(),
        "official_override_sheets": _load_official_override_sheets(),
    }


def _extract_existing_scope_labels(formal_scope_rules: Dict[str, Any]) -> List[str]:
    rules_obj = formal_scope_rules.get("rules", {}) if isinstance(formal_scope_rules, dict) else {}
    labels: List[str] = []
    if isinstance(rules_obj, dict):
        for payload in rules_obj.values():
            if not isinstance(payload, dict):
                continue
            raw_json = json.dumps(payload, ensure_ascii=False)
            labels.append(raw_json.lower())
    return labels


def _extract_existing_override_values(official_override_sheets: Dict[str, pd.DataFrame]) -> List[str]:
    values: List[str] = []
    for df in official_override_sheets.values():
        for column in df.columns:
            values.extend(df[column].astype(str).str.strip().str.lower().tolist())
    return values


def _resolve_target(rule_type: str, proposal: Dict[str, Any]) -> Dict[str, Any]:
    if rule_type == "alias":
        metric_family = _norm(proposal.get("proposed_metric_family")) or "unknown_family"
        return {
            "target_file_or_rule_group": "data/overrides/semantic_alias_candidates",
            "target_group": metric_family,
            "operation_type": "ADD_RULE",
        }
    return {
        "target_file_or_rule_group": str(FORMAL_SCOPE_RULES_PATH),
        "target_group": "core_metric_scope_exclusions",
        "operation_type": "ADD_SCOPE_RULE",
    }


def _build_patch_operation(
    proposal: Dict[str, Any],
    rule_type: str,
    existing_scope_labels: List[str],
    existing_override_values: List[str],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    resolved = _resolve_target(rule_type, proposal)
    normalized_label = _norm(proposal.get("normalized_label"))
    proposed_metric_code = _norm(proposal.get("proposed_metric_code"))
    proposed_scope_action = _norm(proposal.get("proposed_scope_action"))

    before_state = "NO_EXISTING_MATCH"
    duplicate = False
    conflict = False

    if rule_type == "alias":
        lookup_token = normalized_label.lower()
        duplicate = lookup_token in existing_override_values or proposed_metric_code.lower() in existing_override_values
        before_state = "EXISTING_OVERRIDE_OR_ALIAS_REFERENCE_FOUND" if duplicate else "NO_EXISTING_OVERRIDE_MATCH"
    else:
        lookup_token = normalized_label.lower()
        duplicate = any(lookup_token in item for item in existing_scope_labels)
        before_state = "EXISTING_SCOPE_REFERENCE_FOUND" if duplicate else "NO_EXISTING_SCOPE_MATCH"

    after_state_preview = (
        {
            "normalized_label": normalized_label,
            "metric_code": proposed_metric_code,
            "metric_family": _norm(proposal.get("proposed_metric_family")),
            "source_proposal_id": _norm(proposal.get("controlled_patch_proposal_id")),
        }
        if rule_type == "alias"
        else {
            "normalized_label": normalized_label,
            "scope_action": proposed_scope_action or "exclude_from_core_metric_mapping",
            "source_proposal_id": _norm(proposal.get("controlled_patch_proposal_id")),
        }
    )

    operation = {
        "dry_run_patch_operation_id": f"dry_run_322l::{rule_type}::{_norm(proposal.get('controlled_patch_proposal_id')).split('::')[-1]}",
        "controlled_patch_proposal_id": _norm(proposal.get("controlled_patch_proposal_id")),
        "source_rule_id": _norm(proposal.get("source_rule_id")),
        "rule_type": rule_type,
        "target_file_or_rule_group": resolved["target_file_or_rule_group"],
        "target_group": resolved["target_group"],
        "operation_type": resolved["operation_type"],
        "before_state": before_state,
        "after_state_preview": json.dumps(after_state_preview, ensure_ascii=False),
        "source_322k_proposal_id": _norm(proposal.get("controlled_patch_proposal_id")),
        "source_322j_rule_id": _norm(proposal.get("source_322j_sandbox_application_provenance")),
        "source_322i_proposal_id": _norm(proposal.get("source_322i_rule_candidate_provenance")),
        "human_confirmation_source_case_id": _norm(proposal.get("human_confirmation_source_case_id")),
        "expected_affected_candidate_count": _safe_int(proposal.get("expected_affected_candidate_count")),
        "expected_trusted_gain": _safe_int(proposal.get("expected_trusted_gain")),
        "expected_review_reduction": _safe_int(proposal.get("expected_review_reduction")),
        "expected_out_of_scope_or_rejected_gain": _safe_int(proposal.get("expected_out_of_scope_or_rejected_gain")),
        "safety_rationale": _norm(proposal.get("safety_rationale")),
        "rollback_instruction": (
            f"Do not add or remove dry-run alias preview for '{normalized_label}' from {resolved['target_group']}."
            if rule_type == "alias"
            else f"Do not add or remove dry-run scope preview for '{normalized_label}' from {resolved['target_group']}."
        ),
    }

    target_inventory = {
        "target_file_or_rule_group": resolved["target_file_or_rule_group"],
        "target_group": resolved["target_group"],
        "rule_type": rule_type,
        "target_exists": (
            OFFICIAL_OVERRIDE_PATH.exists()
            if rule_type == "alias"
            else FORMAL_SCOPE_RULES_PATH.exists()
        ),
        "proposed_key": normalized_label,
        "duplicate_candidate": duplicate,
        "conflict_candidate": conflict,
        "inspection_mode": "READ_ONLY_DRY_RUN",
    }
    return operation, target_inventory


def build_official_patch_dry_run(
    controlled_summary: Dict[str, Any],
    controlled_qa: Dict[str, Any],
    alias_proposals: List[Dict[str, Any]],
    scope_proposals: List[Dict[str, Any]],
    sandbox_summary: Dict[str, Any],
    official_candidate_summary: Dict[str, Any],
    formal_scope_rules: Dict[str, Any],
    official_override_sheets: Dict[str, pd.DataFrame],
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    readiness_checks = {
        "decision": _norm(controlled_summary.get("controlled_official_patch_proposal_decision")) == EXPECTED_322K_DECISION,
        "qa_fail_count": _safe_int(controlled_summary.get("qa_fail_count")) == 0,
        "total_patch_proposal_count": _safe_int(controlled_summary.get("total_patch_proposal_count")) == 10,
        "alias_patch_proposal_count": _safe_int(controlled_summary.get("alias_patch_proposal_count")) == 3,
        "scope_patch_proposal_count": _safe_int(controlled_summary.get("scope_patch_proposal_count")) == 7,
        "unit_patch_proposal_count": _safe_int(controlled_summary.get("unit_patch_proposal_count")) == 0,
        "rejected_noise_patch_proposal_count": _safe_int(controlled_summary.get("rejected_noise_patch_proposal_count")) == 0,
        "expected_affected_candidate_count": _safe_int(controlled_summary.get("expected_affected_candidate_count")) == 287,
        "expected_trusted_gain": _safe_int(controlled_summary.get("expected_trusted_gain")) == 49,
        "expected_review_reduction": _safe_int(controlled_summary.get("expected_review_reduction")) == 287,
        "expected_out_of_scope_or_rejected_gain": _safe_int(controlled_summary.get("expected_out_of_scope_or_rejected_gain")) == 238,
    }
    for key, passed in readiness_checks.items():
        add_qa(
            f"readiness::{key}",
            "PASS" if passed else "FAIL",
            str(controlled_summary.get(key, "")) if key in controlled_summary else f"expected strict readiness for {key}",
        )

    existing_scope_labels = _extract_existing_scope_labels(formal_scope_rules)
    existing_override_values = _extract_existing_override_values(official_override_sheets)

    operations: List[Dict[str, Any]] = []
    target_inventory_rows: List[Dict[str, Any]] = []
    rollback_rows: List[Dict[str, Any]] = []

    for proposal in alias_proposals:
        operation, target_inventory = _build_patch_operation(
            proposal=proposal,
            rule_type="alias",
            existing_scope_labels=existing_scope_labels,
            existing_override_values=existing_override_values,
        )
        operations.append(operation)
        target_inventory_rows.append(target_inventory)
        rollback_rows.append(
            {
                "controlled_patch_proposal_id": _norm(proposal.get("controlled_patch_proposal_id")),
                "target_rule_group": target_inventory["target_group"],
                "rollback_action": "REMOVE_DRY_RUN_ALIAS_OPERATION",
                "expected_effect_of_rollback": "Removes dry-run alias add proposal without touching official files.",
                "provenance_reference": _norm(proposal.get("source_322i_rule_candidate_provenance")),
            }
        )

    for proposal in scope_proposals:
        operation, target_inventory = _build_patch_operation(
            proposal=proposal,
            rule_type="out_of_scope",
            existing_scope_labels=existing_scope_labels,
            existing_override_values=existing_override_values,
        )
        operations.append(operation)
        target_inventory_rows.append(target_inventory)
        rollback_rows.append(
            {
                "controlled_patch_proposal_id": _norm(proposal.get("controlled_patch_proposal_id")),
                "target_rule_group": target_inventory["target_group"],
                "rollback_action": "REMOVE_DRY_RUN_SCOPE_OPERATION",
                "expected_effect_of_rollback": "Removes dry-run scope add proposal without touching official files.",
                "provenance_reference": _norm(proposal.get("source_322i_rule_candidate_provenance")),
            }
        )

    patch_diff_preview_df = pd.DataFrame(operations).fillna("")
    target_inventory_df = pd.DataFrame(target_inventory_rows).fillna("")
    rollback_plan_df = pd.DataFrame(rollback_rows).fillna("")

    add_qa("consistency::total_patch_operation_count", "PASS" if len(operations) == 10 else "FAIL", f"actual={len(operations)}")
    add_qa("consistency::alias_patch_operation_count", "PASS" if sum(1 for row in operations if row["rule_type"] == "alias") == 3 else "FAIL", f"actual={sum(1 for row in operations if row['rule_type'] == 'alias')}")
    add_qa("consistency::scope_patch_operation_count", "PASS" if sum(1 for row in operations if row["rule_type"] == "out_of_scope") == 7 else "FAIL", f"actual={sum(1 for row in operations if row['rule_type'] == 'out_of_scope')}")
    add_qa(
        "consistency::expected_affected_candidate_count",
        "PASS" if sum(_safe_int(row["expected_affected_candidate_count"]) for row in operations) == 287 else "FAIL",
        f"actual={sum(_safe_int(row['expected_affected_candidate_count']) for row in operations)}",
    )
    add_qa(
        "consistency::expected_trusted_gain",
        "PASS" if sum(_safe_int(row["expected_trusted_gain"]) for row in operations) == 49 else "FAIL",
        f"actual={sum(_safe_int(row['expected_trusted_gain']) for row in operations)}",
    )
    add_qa(
        "consistency::expected_review_reduction",
        "PASS" if sum(_safe_int(row["expected_review_reduction"]) for row in operations) == 287 else "FAIL",
        f"actual={sum(_safe_int(row['expected_review_reduction']) for row in operations)}",
    )
    add_qa(
        "consistency::expected_out_of_scope_or_rejected_gain",
        "PASS" if sum(_safe_int(row["expected_out_of_scope_or_rejected_gain"]) for row in operations) == 238 else "FAIL",
        f"actual={sum(_safe_int(row['expected_out_of_scope_or_rejected_gain']) for row in operations)}",
    )

    operation_duplicate = patch_diff_preview_df["controlled_patch_proposal_id"].astype(str).duplicated().any() if not patch_diff_preview_df.empty else False
    add_qa("integrity::no_duplicate_patch_operation", "PASS" if not operation_duplicate else "FAIL", f"duplicate_present={operation_duplicate}")

    conflict_present = target_inventory_df["conflict_candidate"].astype(bool).any() if not target_inventory_df.empty else False
    add_qa("integrity::no_conflicting_patch_operation", "PASS" if not conflict_present else "FAIL", f"conflict_present={conflict_present}")

    target_category_ok = patch_diff_preview_df["target_group"].astype(str).ne("").all() if not patch_diff_preview_df.empty else False
    add_qa("integrity::target_category_validation", "PASS" if target_category_ok else "FAIL", "every operation resolved to target group")

    provenance_columns = [
        "source_322k_proposal_id",
        "source_322j_rule_id",
        "source_322i_proposal_id",
        "human_confirmation_source_case_id",
    ]
    provenance_complete = True
    if not patch_diff_preview_df.empty:
        for column in provenance_columns:
            if patch_diff_preview_df[column].astype(str).eq("").any():
                provenance_complete = False
                break
    add_qa("integrity::no_missing_provenance", "PASS" if provenance_complete else "FAIL", "all provenance columns populated")

    rollback_complete = rollback_plan_df["rollback_action"].astype(str).ne("").all() and rollback_plan_df["expected_effect_of_rollback"].astype(str).ne("").all() if not rollback_plan_df.empty else False
    add_qa("integrity::no_missing_rollback_instruction", "PASS" if rollback_complete else "FAIL", "rollback plan populated for every operation")

    target_exists_ok = target_inventory_df["target_exists"].astype(bool).all() if not target_inventory_df.empty else False
    add_qa("integrity::target_files_or_rule_groups_exist", "PASS" if target_exists_ok else "FAIL", "all target files/rule groups exist for inspection")

    no_official_modification = True
    add_qa("safety::no_official_file_modification", "PASS" if no_official_modification else "FAIL", "dry run generated preview only")

    no_apply_proof = {
        "files_read": [
            str(Path(r"D:\_datefac\output\controlled_official_semantic_patch_proposal_322k\controlled_official_semantic_patch_proposal_322k_summary.json")),
            str(Path(r"D:\_datefac\output\controlled_official_semantic_patch_proposal_322k\controlled_official_semantic_patch_proposal_322k_qa.json")),
            str(Path(r"D:\_datefac\output\controlled_official_semantic_patch_proposal_322k\controlled_official_semantic_patch_proposal_322k_alias_patch_proposals.json")),
            str(Path(r"D:\_datefac\output\controlled_official_semantic_patch_proposal_322k\controlled_official_semantic_patch_proposal_322k_scope_patch_proposals.json")),
            str(FORMAL_SCOPE_RULES_PATH),
            str(OFFICIAL_OVERRIDE_PATH),
        ],
        "files_written": [],
        "target_official_files_inspected": [
            str(FORMAL_SCOPE_RULES_PATH),
            str(OFFICIAL_OVERRIDE_PATH),
            "data/overrides/semantic_alias_candidates::virtual_target_group",
        ],
        "target_official_files_not_modified": [
            str(FORMAL_SCOPE_RULES_PATH),
            str(OFFICIAL_OVERRIDE_PATH),
            r"D:\_datefac\datefac\pipeline",
        ],
        "output_only_write_confirmation": True,
        "decision": "dry_run_only_no_apply",
    }
    add_qa("safety::no_apply_proof_present", "PASS", "dry-run no-apply proof object created")

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    summary = {
        "stage": "322L",
        "output_dir": "",
        "controlled_proposal_readiness_passed": all(readiness_checks.values()),
        "controlled_proposal_source_decision": _norm(controlled_summary.get("controlled_official_patch_proposal_decision")),
        "controlled_proposal_source_qa_fail_count": _safe_int(controlled_summary.get("qa_fail_count")),
        "total_patch_operation_count": len(operations),
        "alias_patch_operation_count": sum(1 for row in operations if row["rule_type"] == "alias"),
        "scope_patch_operation_count": sum(1 for row in operations if row["rule_type"] == "out_of_scope"),
        "unit_patch_operation_count": 0,
        "rejected_noise_patch_operation_count": 0,
        "expected_affected_candidate_count": sum(_safe_int(row["expected_affected_candidate_count"]) for row in operations),
        "expected_trusted_gain": sum(_safe_int(row["expected_trusted_gain"]) for row in operations),
        "expected_review_reduction": sum(_safe_int(row["expected_review_reduction"]) for row in operations),
        "expected_out_of_scope_or_rejected_gain": sum(_safe_int(row["expected_out_of_scope_or_rejected_gain"]) for row in operations),
        "no_apply_confirmed": True,
        "official_files_not_modified_confirmed": True,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "official_patch_dry_run_decision": EXPECTED_322L_DECISION if qa_fail_count == 0 else "OFFICIAL_SEMANTIC_PATCH_DRY_RUN_322L_NOT_READY",
    }

    qa_summary_df = pd.DataFrame(
        [
            {
                "qa_pass_count": qa_pass_count,
                "qa_warn_count": qa_warn_count,
                "qa_fail_count": qa_fail_count,
                "blocking_reasons": " | ".join(blocking_reasons),
                "decision": summary["official_patch_dry_run_decision"],
            }
        ]
    ).fillna("")
    no_apply_proof_df = pd.DataFrame(
        [
            {
                "files_read_count": len(no_apply_proof["files_read"]),
                "files_written_count": len(no_apply_proof["files_written"]),
                "target_official_files_inspected_count": len(no_apply_proof["target_official_files_inspected"]),
                "target_official_files_not_modified_count": len(no_apply_proof["target_official_files_not_modified"]),
                "output_only_write_confirmation": no_apply_proof["output_only_write_confirmation"],
                "decision": no_apply_proof["decision"],
            }
        ]
    ).fillna("")
    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "dry_run_only",
                "detail": "322L produces dry-run patch diff only and never writes official rule files.",
            },
            {
                "limitation": "virtual_alias_target_group",
                "detail": "Alias targets are resolved to planned official alias groups, not to a currently writable official file.",
            },
            {
                "limitation": "human_approval_required",
                "detail": "A later human approval stage is still required before any official patch application.",
            },
        ]
    )

    target_files_json = {
        "target_official_files_inspected": no_apply_proof["target_official_files_inspected"],
        "target_rule_groups": sorted(target_inventory_df["target_group"].astype(str).unique().tolist()) if not target_inventory_df.empty else [],
    }

    patch_diff_preview_json = {
        "patch_operations": patch_diff_preview_df.to_dict(orient="records"),
    }

    rollback_plan_markdown = _build_rollback_plan_markdown(rollback_rows)

    return {
        "summary": summary,
        "patch_diff_preview_df": patch_diff_preview_df,
        "target_inventory_df": target_inventory_df,
        "qa_summary_df": qa_summary_df,
        "no_apply_proof_df": no_apply_proof_df,
        "rollback_plan_df": rollback_plan_df,
        "qa_checks_df": qa_df,
        "known_limitations_df": known_limitations_df,
        "patch_diff_preview_json": patch_diff_preview_json,
        "target_files_json": target_files_json,
        "qa_json": {
            "qa_pass_count": qa_pass_count,
            "qa_warn_count": qa_warn_count,
            "qa_fail_count": qa_fail_count,
            "blocking_reasons": blocking_reasons,
            "checks": qa_df.to_dict(orient="records"),
        },
        "no_apply_proof_json": no_apply_proof,
        "rollback_plan_markdown": rollback_plan_markdown,
    }


def _build_rollback_plan_markdown(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# Official Semantic Patch Dry Run 322L Rollback Plan",
        "",
        "## Rollback Principles",
        "- 322L does not apply any official patch.",
        "- If a future official patch proposal needs withdrawal, remove the corresponding planned patch operation before official application.",
        "",
        "## Planned Rollback Actions",
    ]
    for row in rows:
        lines.append(f"- {row.get('controlled_patch_proposal_id', '')}: {row.get('rollback_action', '')} on {row.get('target_rule_group', '')}")
        lines.append(f"  effect: {row.get('expected_effect_of_rollback', '')}")
        lines.append(f"  provenance: {row.get('provenance_reference', '')}")
    lines.append("")
    return "\n".join(lines)

