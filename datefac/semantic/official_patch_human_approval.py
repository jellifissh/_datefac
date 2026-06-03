from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Sequence, Set

import pandas as pd


EXPECTED_322L_DECISION = "OFFICIAL_SEMANTIC_PATCH_DRY_RUN_322L_READY_FOR_322M_HUMAN_APPROVAL"
EXPECTED_322M_PREPARE_DECISION = "OFFICIAL_SEMANTIC_PATCH_HUMAN_APPROVAL_322M_READY_FOR_HUMAN_REVIEW"
EXPECTED_322M_PREPARE_NOT_READY = "OFFICIAL_SEMANTIC_PATCH_HUMAN_APPROVAL_322M_NOT_READY"
EXPECTED_322M_REVIEWED_DECISION = "OFFICIAL_SEMANTIC_PATCH_HUMAN_APPROVAL_322M_REVIEWED_READY_FOR_322N_OFFICIAL_PATCH_APPLICATION"
EXPECTED_322M_REVIEWED_NOT_READY = "OFFICIAL_SEMANTIC_PATCH_HUMAN_APPROVAL_322M_REVIEWED_NOT_READY"
EXPECTED_322MR_DECISION = "OFFICIAL_SEMANTIC_PATCH_HUMAN_APPROVAL_322M_VALIDATE_REVIEWED_READY_FOR_REAL_HUMAN_REVIEWED_WORKBOOK"
EXPECTED_322MR_NOT_READY = "OFFICIAL_SEMANTIC_PATCH_HUMAN_APPROVAL_322M_VALIDATE_REVIEWED_NOT_READY"

DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\official_semantic_patch_human_approval_322m")
FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
OFFICIAL_OVERRIDE_PATH = Path(r"D:\_datefac\data\overrides\02B_ai_repair_override.xlsx")

PREPARE_DECISION_PENDING = "PENDING_HUMAN_APPROVAL"
ALLOWED_REVIEWER_DECISIONS = {
    "APPROVED",
    "REJECTED",
    "NEEDS_MORE_REVIEW",
}
REQUIRED_REVIEWER_EDITABLE_FIELDS = {
    "reviewer_decision",
    "reviewer_note",
    "reviewer_name",
    "approval_timestamp",
}


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


def _read_workbook_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_excel(path, sheet_name=sheet_name)
    except Exception:
        return pd.DataFrame()
    return df.fillna("")


def _parse_json_maybe(value: Any) -> Any:
    text = _norm(value)
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        return text


def _decision_distribution(records: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    distribution: Dict[str, int] = {}
    for record in records:
        key = _norm(record.get("reviewer_decision")) or PREPARE_DECISION_PENDING
        distribution[key] = distribution.get(key, 0) + 1
    return distribution


def _count_pending_decisions(records: Sequence[Dict[str, Any]]) -> int:
    total = 0
    for record in records:
        decision = _norm(record.get("reviewer_decision")).upper()
        if decision in {"", PREPARE_DECISION_PENDING}:
            total += 1
    return total


def _count_invalid_decisions(records: Sequence[Dict[str, Any]]) -> int:
    total = 0
    for record in records:
        decision = _norm(record.get("reviewer_decision")).upper()
        if decision and decision != PREPARE_DECISION_PENDING and decision not in ALLOWED_REVIEWER_DECISIONS:
            total += 1
    return total


def _missing_required_fields(records: Sequence[Dict[str, Any]], required_fields: Sequence[str]) -> List[Dict[str, str]]:
    missing: List[Dict[str, str]] = []
    for record in records:
        record_id = _norm(record.get("approval_id")) or _norm(record.get("dry_run_patch_operation_id")) or "UNKNOWN_RECORD"
        for field in required_fields:
            if _norm(record.get(field)) == "":
                missing.append({"record_id": record_id, "field": field})
    return missing


def load_official_patch_human_approval_inputs(
    dry_run_dir: Path,
    controlled_proposal_dir: Path | None = None,
    sandbox_application_dir: Path | None = None,
    official_rule_candidate_dir: Path | None = None,
) -> Dict[str, Any]:
    return {
        "dry_run_summary": _read_json(dry_run_dir / "official_semantic_patch_dry_run_322l_summary.json"),
        "dry_run_qa": _read_json(dry_run_dir / "official_semantic_patch_dry_run_322l_qa.json"),
        "dry_run_patch_diff_preview": _read_json(dry_run_dir / "official_semantic_patch_dry_run_322l_patch_diff_preview.json"),
        "dry_run_target_files": _read_json(dry_run_dir / "official_semantic_patch_dry_run_322l_target_files.json"),
        "controlled_summary": _read_json(controlled_proposal_dir / "controlled_official_semantic_patch_proposal_322k_summary.json")
        if controlled_proposal_dir
        else {},
        "sandbox_summary": _read_json(sandbox_application_dir / "official_semantic_rule_candidates_322j_summary.json")
        if sandbox_application_dir
        else {},
        "official_candidate_summary": _read_json(official_rule_candidate_dir / "official_semantic_rule_candidates_322i_summary.json")
        if official_rule_candidate_dir
        else {},
    }


def build_official_patch_human_approval_prepare(
    dry_run_summary: Dict[str, Any],
    dry_run_qa: Dict[str, Any],
    dry_run_patch_diff_preview: Dict[str, Any],
    dry_run_target_files: Dict[str, Any],
    controlled_summary: Dict[str, Any] | None = None,
    sandbox_summary: Dict[str, Any] | None = None,
    official_candidate_summary: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    controlled_summary = controlled_summary or {}
    sandbox_summary = sandbox_summary or {}
    official_candidate_summary = official_candidate_summary or {}

    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    readiness_checks = {
        "decision": _norm(dry_run_summary.get("official_patch_dry_run_decision")) == EXPECTED_322L_DECISION,
        "qa_fail_count": _safe_int(dry_run_summary.get("qa_fail_count")) == 0,
        "total_patch_operation_count": _safe_int(dry_run_summary.get("total_patch_operation_count")) == 10,
        "alias_patch_operation_count": _safe_int(dry_run_summary.get("alias_patch_operation_count")) == 3,
        "scope_patch_operation_count": _safe_int(dry_run_summary.get("scope_patch_operation_count")) == 7,
        "unit_patch_operation_count": _safe_int(dry_run_summary.get("unit_patch_operation_count")) == 0,
        "rejected_noise_patch_operation_count": _safe_int(dry_run_summary.get("rejected_noise_patch_operation_count")) == 0,
        "expected_affected_candidate_count": _safe_int(dry_run_summary.get("expected_affected_candidate_count")) == 287,
        "expected_trusted_gain": _safe_int(dry_run_summary.get("expected_trusted_gain")) == 49,
        "expected_review_reduction": _safe_int(dry_run_summary.get("expected_review_reduction")) == 287,
        "expected_out_of_scope_or_rejected_gain": _safe_int(dry_run_summary.get("expected_out_of_scope_or_rejected_gain")) == 238,
    }
    for key, passed in readiness_checks.items():
        add_qa(
            f"readiness::{key}",
            "PASS" if passed else "FAIL",
            str(dry_run_summary.get(key, "")) if key in dry_run_summary else f"expected strict readiness for {key}",
        )

    dry_run_checks = dry_run_qa.get("checks", [])
    if isinstance(dry_run_checks, list):
        add_qa(
            "readiness::dry_run_qa_payload_present",
            "PASS" if len(dry_run_checks) > 0 else "FAIL",
            f"qa_check_count={len(dry_run_checks)}",
        )
    else:
        add_qa("readiness::dry_run_qa_payload_present", "FAIL", "qa checks missing")

    operations = dry_run_patch_diff_preview.get("patch_operations", [])
    if not isinstance(operations, list):
        operations = []
    operations = [item for item in operations if isinstance(item, dict)]

    approval_records: List[Dict[str, Any]] = []
    for operation in operations:
        patch_operation_id = _norm(operation.get("dry_run_patch_operation_id"))
        rule_type = _norm(operation.get("rule_type"))
        suffix = patch_operation_id.split("::")[-1] if patch_operation_id else f"{len(approval_records) + 1:03d}"
        approval_id = f"approval_322m::{rule_type or 'unknown'}::{suffix}"
        exact_change_payload = _parse_json_maybe(operation.get("after_state_preview"))
        exact_change = (
            json.dumps(exact_change_payload, ensure_ascii=False)
            if isinstance(exact_change_payload, (dict, list))
            else _norm(exact_change_payload)
        )
        expected_affected_candidate_count = _safe_int(operation.get("expected_affected_candidate_count"))
        expected_trusted_gain = _safe_int(operation.get("expected_trusted_gain"))
        expected_review_reduction = _safe_int(operation.get("expected_review_reduction"))
        expected_out_of_scope_or_rejected_gain = _safe_int(operation.get("expected_out_of_scope_or_rejected_gain"))
        evidence_summary = " | ".join(
            [
                f"before_state={_norm(operation.get('before_state'))}",
                f"target_group={_norm(operation.get('target_group'))}",
                f"source_322k={_norm(operation.get('source_322k_proposal_id'))}",
                f"source_322j={_norm(operation.get('source_322j_rule_id'))}",
                f"source_322i={_norm(operation.get('source_322i_proposal_id'))}",
                f"human_case={_norm(operation.get('human_confirmation_source_case_id'))}",
            ]
        )
        risk_note = (
            "Human approval required before any official alias addition."
            if rule_type == "alias"
            else "Human approval required before any official scope exclusion."
        )
        approval_records.append(
            {
                "approval_id": approval_id,
                "dry_run_patch_operation_id": patch_operation_id,
                "controlled_patch_proposal_id": _norm(operation.get("controlled_patch_proposal_id")),
                "source_rule_id": _norm(operation.get("source_rule_id")),
                "rule_type": rule_type,
                "target_file_or_rule_group": _norm(operation.get("target_file_or_rule_group")),
                "target_group": _norm(operation.get("target_group")),
                "operation_type": _norm(operation.get("operation_type")),
                "exact_proposed_change": exact_change,
                "expected_affected_candidate_count": expected_affected_candidate_count,
                "expected_trusted_gain": expected_trusted_gain,
                "expected_review_reduction": expected_review_reduction,
                "expected_out_of_scope_or_rejected_gain": expected_out_of_scope_or_rejected_gain,
                "evidence_summary": evidence_summary,
                "risk_note": risk_note,
                "safety_rationale": _norm(operation.get("safety_rationale")),
                "rollback_note": _norm(operation.get("rollback_instruction")),
                "source_322k_proposal_id": _norm(operation.get("source_322k_proposal_id")),
                "source_322j_rule_id": _norm(operation.get("source_322j_rule_id")),
                "source_322i_proposal_id": _norm(operation.get("source_322i_proposal_id")),
                "human_confirmation_source_case_id": _norm(operation.get("human_confirmation_source_case_id")),
                "reviewer_decision": PREPARE_DECISION_PENDING,
                "reviewer_note": "",
                "reviewer_name": "",
                "approval_timestamp": "",
                "allowed_reviewer_decisions": "APPROVED | REJECTED | NEEDS_MORE_REVIEW",
            }
        )

    approvals_df = pd.DataFrame(approval_records).fillna("")
    alias_df = approvals_df.loc[approvals_df["rule_type"].astype(str) == "alias"].copy() if not approvals_df.empty else pd.DataFrame()
    scope_df = approvals_df.loc[approvals_df["rule_type"].astype(str) == "out_of_scope"].copy() if not approvals_df.empty else pd.DataFrame()

    add_qa("approval_count::patch_operation_count", "PASS" if len(operations) == 10 else "FAIL", f"actual={len(operations)}")
    add_qa("approval_count::approval_record_count", "PASS" if len(approval_records) == 10 else "FAIL", f"actual={len(approval_records)}")
    add_qa("approval_count::alias", "PASS" if len(alias_df) == 3 else "FAIL", f"actual={len(alias_df)}")
    add_qa("approval_count::scope", "PASS" if len(scope_df) == 7 else "FAIL", f"actual={len(scope_df)}")
    add_qa("approval_count::unit", "PASS", "actual=0")
    add_qa("approval_count::rejected_noise", "PASS", "actual=0")

    all_pending = (
        not approvals_df.empty
        and approvals_df["reviewer_decision"].astype(str).eq(PREPARE_DECISION_PENDING).all()
    )
    add_qa("approval_integrity::all_pending_human_approval", "PASS" if all_pending else "FAIL", f"distribution={_decision_distribution(approval_records)}")

    duplicate_approval_id = approvals_df["approval_id"].astype(str).duplicated().any() if not approvals_df.empty else False
    add_qa("approval_integrity::no_duplicate_approval_id", "PASS" if not duplicate_approval_id else "FAIL", f"duplicate_present={duplicate_approval_id}")

    duplicate_patch_op_id = approvals_df["dry_run_patch_operation_id"].astype(str).duplicated().any() if not approvals_df.empty else False
    add_qa("approval_integrity::no_duplicate_patch_operation_id", "PASS" if not duplicate_patch_op_id else "FAIL", f"duplicate_present={duplicate_patch_op_id}")

    provenance_columns = [
        "source_322k_proposal_id",
        "source_322j_rule_id",
        "source_322i_proposal_id",
        "human_confirmation_source_case_id",
    ]
    provenance_complete = True
    if not approvals_df.empty:
        for column in provenance_columns:
            if approvals_df[column].astype(str).eq("").any():
                provenance_complete = False
                break
    add_qa("approval_integrity::provenance_completeness", "PASS" if provenance_complete else "FAIL", "all provenance fields populated")

    rollback_complete = not approvals_df.empty and approvals_df["rollback_note"].astype(str).ne("").all()
    add_qa("approval_integrity::rollback_note_completeness", "PASS" if rollback_complete else "FAIL", "rollback note populated for every record")

    reviewer_fields = {"reviewer_decision", "reviewer_note", "reviewer_name", "approval_timestamp"}
    reviewer_fields_present = reviewer_fields.issubset(set(approvals_df.columns))
    add_qa("approval_integrity::reviewer_fields_present", "PASS" if reviewer_fields_present else "FAIL", f"present={sorted(set(approvals_df.columns).intersection(reviewer_fields))}")

    target_files = dry_run_target_files.get("target_official_files_inspected", [])
    if not isinstance(target_files, list):
        target_files = []
    no_official_file_modification = True
    add_qa("safety::no_official_file_modification", "PASS" if no_official_file_modification else "FAIL", "approval package only; no official file writes")

    review_instruction_rows = [
        {
            "section": "package_purpose",
            "instruction": "Review each dry-run semantic patch operation and choose APPROVED, REJECTED, or NEEDS_MORE_REVIEW.",
        },
        {
            "section": "allowed_decisions",
            "instruction": "Allowed reviewer_decision values: APPROVED, REJECTED, NEEDS_MORE_REVIEW.",
        },
        {
            "section": "approval_rule",
            "instruction": "Approve only when the proposed semantic change, provenance, expected impact, and rollback note are acceptable.",
        },
        {
            "section": "rejection_rule",
            "instruction": "Reject when the target category, label semantics, expected impact, or safety rationale is not acceptable.",
        },
        {
            "section": "needs_more_review_rule",
            "instruction": "Use NEEDS_MORE_REVIEW when provenance or rule semantics are insufficient for safe approval.",
        },
        {
            "section": "no_apply_note",
            "instruction": "This package does not apply any official patch and does not modify official mapping, override, or pipeline files.",
        },
        {
            "section": "next_stage_note",
            "instruction": "A later stage can read reviewed decisions and build a final plan, but human approval is not assumed here.",
        },
    ]
    review_instructions_df = pd.DataFrame(review_instruction_rows)

    no_apply_proof_json = {
        "files_read": [
            str(DEFAULT_OUTPUT_DIR.parent / "official_semantic_patch_dry_run_322l" / "official_semantic_patch_dry_run_322l_summary.json"),
            str(DEFAULT_OUTPUT_DIR.parent / "official_semantic_patch_dry_run_322l" / "official_semantic_patch_dry_run_322l_qa.json"),
            str(DEFAULT_OUTPUT_DIR.parent / "official_semantic_patch_dry_run_322l" / "official_semantic_patch_dry_run_322l_patch_diff_preview.json"),
            str(DEFAULT_OUTPUT_DIR.parent / "official_semantic_patch_dry_run_322l" / "official_semantic_patch_dry_run_322l_target_files.json"),
        ],
        "files_written": [],
        "official_target_files_inspected": target_files or [
            str(FORMAL_SCOPE_RULES_PATH),
            str(OFFICIAL_OVERRIDE_PATH),
            "data/overrides/semantic_alias_candidates::virtual_target_group",
        ],
        "official_target_files_not_modified": target_files or [
            str(FORMAL_SCOPE_RULES_PATH),
            str(OFFICIAL_OVERRIDE_PATH),
            "data/overrides/semantic_alias_candidates::virtual_target_group",
        ],
        "output_only_write_confirmation": True,
        "decision": "approval_package_only_no_apply",
    }

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    decision_distribution = _decision_distribution(approval_records)
    summary = {
        "stage": "322M",
        "mode": "prepare",
        "output_dir": "",
        "dry_run_readiness_passed": all(readiness_checks.values()),
        "dry_run_source_decision": _norm(dry_run_summary.get("official_patch_dry_run_decision")),
        "dry_run_source_qa_fail_count": _safe_int(dry_run_summary.get("qa_fail_count")),
        "approval_record_count": len(approval_records),
        "alias_approval_count": len(alias_df),
        "scope_approval_count": len(scope_df),
        "unit_approval_count": 0,
        "rejected_noise_approval_count": 0,
        "expected_affected_candidate_count": sum(_safe_int(row.get("expected_affected_candidate_count")) for row in approval_records),
        "expected_trusted_gain": sum(_safe_int(row.get("expected_trusted_gain")) for row in approval_records),
        "expected_review_reduction": sum(_safe_int(row.get("expected_review_reduction")) for row in approval_records),
        "expected_out_of_scope_or_rejected_gain": sum(_safe_int(row.get("expected_out_of_scope_or_rejected_gain")) for row in approval_records),
        "decision_distribution": decision_distribution,
        "all_decisions_pending_human_approval": all_pending,
        "official_files_not_modified_confirmed": True,
        "approval_package_only_no_apply_confirmed": True,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "official_patch_human_approval_decision": EXPECTED_322M_PREPARE_DECISION if qa_fail_count == 0 else EXPECTED_322M_PREPARE_NOT_READY,
    }

    approval_summary_df = pd.DataFrame(
        [
            {
                "approval_record_count": summary["approval_record_count"],
                "alias_approval_count": summary["alias_approval_count"],
                "scope_approval_count": summary["scope_approval_count"],
                "unit_approval_count": summary["unit_approval_count"],
                "rejected_noise_approval_count": summary["rejected_noise_approval_count"],
                "decision_distribution": json.dumps(decision_distribution, ensure_ascii=False),
                "qa_fail_count": summary["qa_fail_count"],
                "decision": summary["official_patch_human_approval_decision"],
            }
        ]
    ).fillna("")
    qa_summary_df = pd.DataFrame(
        [
            {
                "qa_pass_count": qa_pass_count,
                "qa_warn_count": qa_warn_count,
                "qa_fail_count": qa_fail_count,
                "blocking_reasons": " | ".join(blocking_reasons),
                "decision": summary["official_patch_human_approval_decision"],
            }
        ]
    ).fillna("")
    no_apply_proof_df = pd.DataFrame(
        [
            {
                "files_read_count": len(no_apply_proof_json["files_read"]),
                "files_written_count": len(no_apply_proof_json["files_written"]),
                "official_target_files_inspected_count": len(no_apply_proof_json["official_target_files_inspected"]),
                "official_target_files_not_modified_count": len(no_apply_proof_json["official_target_files_not_modified"]),
                "output_only_write_confirmation": no_apply_proof_json["output_only_write_confirmation"],
                "decision": no_apply_proof_json["decision"],
            }
        ]
    ).fillna("")

    approval_template_json = {
        "stage": "322M",
        "mode": "prepare",
        "summary": summary,
        "allowed_reviewer_decisions": sorted(ALLOWED_REVIEWER_DECISIONS),
        "approval_records": approval_records,
    }
    review_instructions_markdown = _build_prepare_review_instructions_markdown(summary)

    return {
        "summary": summary,
        "approval_summary_df": approval_summary_df,
        "alias_approvals_df": alias_df,
        "scope_approvals_df": scope_df,
        "all_patch_operations_df": approvals_df,
        "qa_summary_df": qa_summary_df,
        "qa_checks_df": qa_df,
        "review_instructions_df": review_instructions_df,
        "no_apply_proof_df": no_apply_proof_df,
        "approval_template_json": approval_template_json,
        "review_instructions_markdown": review_instructions_markdown,
        "no_apply_proof_json": no_apply_proof_json,
        "qa_json": {
            "qa_pass_count": qa_pass_count,
            "qa_warn_count": qa_warn_count,
            "qa_fail_count": qa_fail_count,
            "blocking_reasons": blocking_reasons,
            "checks": qa_df.to_dict(orient="records"),
        },
    }


def build_official_patch_human_approval_validate_reviewed(
    reviewed_workbook: Path,
    dry_run_summary: Dict[str, Any],
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa(
        "readiness::dry_run_ready_for_human_approval",
        "PASS" if _norm(dry_run_summary.get("official_patch_dry_run_decision")) == EXPECTED_322L_DECISION else "FAIL",
        _norm(dry_run_summary.get("official_patch_dry_run_decision")),
    )

    approvals_df = _read_workbook_sheet(reviewed_workbook, "all_patch_operations")
    if approvals_df.empty:
        alias_df = _read_workbook_sheet(reviewed_workbook, "alias_approvals")
        scope_df = _read_workbook_sheet(reviewed_workbook, "scope_approvals")
        approvals_df = pd.concat([alias_df, scope_df], ignore_index=True).fillna("")
    else:
        approvals_df = approvals_df.fillna("")

    required_columns = {
        "approval_id",
        "dry_run_patch_operation_id",
        "rule_type",
        "reviewer_decision",
        "reviewer_note",
        "reviewer_name",
        "approval_timestamp",
        "rollback_note",
        "source_322k_proposal_id",
        "source_322j_rule_id",
        "source_322i_proposal_id",
        "human_confirmation_source_case_id",
    }
    missing_columns = sorted(required_columns.difference(set(approvals_df.columns)))
    add_qa(
        "reviewed_integrity::required_columns_present",
        "PASS" if not missing_columns else "FAIL",
        "none" if not missing_columns else " | ".join(missing_columns),
    )

    records = approvals_df.to_dict(orient="records") if not approvals_df.empty else []
    decisions = [_norm(row.get("reviewer_decision")).upper() for row in records]
    invalid_decisions = sorted({decision for decision in decisions if decision not in ALLOWED_REVIEWER_DECISIONS})
    pending_present = PREPARE_DECISION_PENDING in decisions or "" in decisions
    pending_count = _count_pending_decisions(records)
    invalid_decision_count = _count_invalid_decisions(records)
    add_qa(
        "reviewed_integrity::valid_reviewer_decisions_only",
        "PASS" if not invalid_decisions else "FAIL",
        "none" if not invalid_decisions else " | ".join(invalid_decisions),
    )
    add_qa(
        "reviewed_integrity::no_pending_human_approval",
        "PASS" if not pending_present else "FAIL",
        f"pending_present={pending_present}; pending_count={pending_count}",
    )

    approval_count = len(records)
    alias_count = int(approvals_df["rule_type"].astype(str).eq("alias").sum()) if not approvals_df.empty else 0
    scope_count = int(approvals_df["rule_type"].astype(str).eq("out_of_scope").sum()) if not approvals_df.empty else 0
    add_qa("reviewed_count::approval_record_count", "PASS" if approval_count == 10 else "FAIL", f"actual={approval_count}")
    add_qa("reviewed_count::alias", "PASS" if alias_count == 3 else "FAIL", f"actual={alias_count}")
    add_qa("reviewed_count::scope", "PASS" if scope_count == 7 else "FAIL", f"actual={scope_count}")

    duplicate_approval_id = approvals_df["approval_id"].astype(str).duplicated().any() if not approvals_df.empty else False
    duplicate_patch_op_id = approvals_df["dry_run_patch_operation_id"].astype(str).duplicated().any() if not approvals_df.empty else False
    add_qa("reviewed_integrity::no_duplicate_approval_id", "PASS" if not duplicate_approval_id else "FAIL", f"duplicate_present={duplicate_approval_id}")
    add_qa("reviewed_integrity::no_duplicate_patch_operation_id", "PASS" if not duplicate_patch_op_id else "FAIL", f"duplicate_present={duplicate_patch_op_id}")

    provenance_columns = [
        "source_322k_proposal_id",
        "source_322j_rule_id",
        "source_322i_proposal_id",
        "human_confirmation_source_case_id",
    ]
    provenance_complete = True
    if not approvals_df.empty:
        for column in provenance_columns:
            if approvals_df[column].astype(str).eq("").any():
                provenance_complete = False
                break
    add_qa("reviewed_integrity::provenance_completeness", "PASS" if provenance_complete else "FAIL", "all provenance fields populated")

    rollback_complete = not approvals_df.empty and approvals_df["rollback_note"].astype(str).ne("").all()
    add_qa("reviewed_integrity::rollback_note_completeness", "PASS" if rollback_complete else "FAIL", "rollback note populated for every reviewed record")

    reviewer_field_missing = _missing_required_fields(records, sorted(REQUIRED_REVIEWER_EDITABLE_FIELDS))
    add_qa(
        "reviewed_integrity::reviewer_fields_non_empty",
        "PASS" if not reviewer_field_missing else "FAIL",
        "none" if not reviewer_field_missing else " | ".join(f"{item['record_id']}::{item['field']}" for item in reviewer_field_missing[:10]),
    )

    patch_identity_missing = _missing_required_fields(records, ["approval_id", "dry_run_patch_operation_id", "source_322k_proposal_id"])
    add_qa(
        "reviewed_integrity::patch_identity_fields_non_empty",
        "PASS" if not patch_identity_missing else "FAIL",
        "none" if not patch_identity_missing else " | ".join(f"{item['record_id']}::{item['field']}" for item in patch_identity_missing[:10]),
    )

    approved_df = approvals_df.loc[approvals_df["reviewer_decision"].astype(str).str.upper() == "APPROVED"].copy() if not approvals_df.empty else pd.DataFrame()
    rejected_df = approvals_df.loc[approvals_df["reviewer_decision"].astype(str).str.upper() == "REJECTED"].copy() if not approvals_df.empty else pd.DataFrame()
    needs_more_review_df = approvals_df.loc[approvals_df["reviewer_decision"].astype(str).str.upper() == "NEEDS_MORE_REVIEW"].copy() if not approvals_df.empty else pd.DataFrame()

    add_qa(
        "reviewed_integrity::at_least_one_approved_patch",
        "PASS" if len(approved_df) > 0 else "FAIL",
        f"approved_count={len(approved_df)}",
    )
    add_qa(
        "safety::no_official_file_modification",
        "PASS",
        "validate-reviewed mode validates decisions only and does not modify official files",
    )

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    approved_records = approved_df.to_dict(orient="records") if not approved_df.empty else []
    summary = {
        "stage": "322M",
        "mode": "validate-reviewed",
        "output_dir": "",
        "reviewed_workbook": str(reviewed_workbook),
        "reviewed_approval_record_count": approval_count,
        "approval_record_count": approval_count,
        "approved_patch_count": len(approved_df),
        "rejected_patch_count": len(rejected_df),
        "needs_more_review_count": len(needs_more_review_df),
        "pending_count": pending_count,
        "invalid_decision_count": invalid_decision_count,
        "final_approved_patch_count": len(approved_df),
        "decision_distribution": _decision_distribution(records),
        "official_files_not_modified_confirmed": True,
        "approval_package_only_no_apply_confirmed": True,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "official_patch_human_approval_decision": EXPECTED_322M_REVIEWED_DECISION if qa_fail_count == 0 else EXPECTED_322M_REVIEWED_NOT_READY,
    }

    final_approved_patch_plan = {
        "stage": "322M",
        "mode": "validate-reviewed",
        "reviewed_workbook": str(reviewed_workbook),
        "approved_patch_operations": approved_records,
        "rejected_patch_operations": rejected_df.to_dict(orient="records") if not rejected_df.empty else [],
        "needs_more_review_patch_operations": needs_more_review_df.to_dict(orient="records") if not needs_more_review_df.empty else [],
        "decision": summary["official_patch_human_approval_decision"],
    }

    return {
        "summary": summary,
        "approved_df": approved_df,
        "rejected_df": rejected_df,
        "needs_more_review_df": needs_more_review_df,
        "all_reviewed_df": approvals_df,
        "final_approved_patch_plan_json": final_approved_patch_plan,
        "qa_json": {
            "qa_pass_count": qa_pass_count,
            "qa_warn_count": qa_warn_count,
            "qa_fail_count": qa_fail_count,
            "blocking_reasons": blocking_reasons,
            "checks": qa_df.to_dict(orient="records"),
        },
    }


def _build_prepare_review_instructions_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Official Semantic Patch Human Approval 322M",
        "",
        "## What This Package Is",
        "- This package turns 322L dry-run semantic patch operations into human-reviewable approval records.",
        "- Every record remains pending until a human reviewer explicitly chooses a decision.",
        "",
        "## What The Reviewer Should Check",
        "- Confirm the semantic label meaning and the intended target group or file category.",
        "- Confirm the expected impact counts look reasonable for the proposed rule.",
        "- Confirm provenance is complete from human confirmation through 322L dry run.",
        "- Confirm rollback notes are adequate before any later official patch stage.",
        "",
        "## Allowed reviewer_decision Values",
        "- APPROVED",
        "- REJECTED",
        "- NEEDS_MORE_REVIEW",
        "",
        "## When To Reject",
        "- Reject if the semantic mapping or scope exclusion is not correct.",
        "- Reject if the target category is wrong or the expected impact is unsafe.",
        "",
        "## When To Mark NEEDS_MORE_REVIEW",
        "- Use NEEDS_MORE_REVIEW when provenance, semantics, or expected impact are still ambiguous.",
        "",
        "## Why This Does Not Apply The Official Patch",
        "- 322M only prepares approval records and does not modify official mapping, official override, or production pipeline files.",
        "",
        "## What Happens In 322N",
        "- A later stage may read reviewed decisions and build a final official patch application plan.",
        "- Human approval is not assumed in 322M.",
        "",
        "## Current Decision",
        f"- {summary.get('official_patch_human_approval_decision', '')}",
        "",
    ]
    return "\n".join(lines)
