from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

import pandas as pd


EXPECTED_324J_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_DRY_RUN_324J_READY_WITH_WARNINGS"
PREPARE_READY_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_HUMAN_APPROVAL_324K_READY_FOR_HUMAN_REVIEW"
REVIEWED_APPROVED_DECISION = (
    "CONTROLLED_OFFICIAL_PROPOSAL_HUMAN_APPROVAL_324K_REVIEWED_READY_FOR_324L_OFFICIAL_PATCH_APPLICATION"
)
REVIEWED_REJECTED_DECISION = (
    "CONTROLLED_OFFICIAL_PROPOSAL_HUMAN_APPROVAL_324K_REVIEWED_REJECTED_NO_OFFICIAL_PATCH_APPLICATION"
)
REVIEWED_NEEDS_INFO_DECISION = (
    "CONTROLLED_OFFICIAL_PROPOSAL_HUMAN_APPROVAL_324K_REVIEWED_NEEDS_MORE_INFO_BLOCKS_OFFICIAL_PATCH_APPLICATION"
)
NOT_READY_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_HUMAN_APPROVAL_324K_NOT_READY"
DEFAULT_OUTPUT_DIR = Path(
    r"D:\_datefac\output\controlled_official_proposal_human_approval_324k"
)
DEFAULT_REVIEWED_OUTPUT_DIR = Path(
    r"D:\_datefac\output\controlled_official_proposal_human_approval_324k_reviewed"
)

PREPARE_DECISION_PENDING = "PENDING_HUMAN_APPROVAL"
ALLOWED_REVIEWER_DECISIONS = {"APPROVE", "REJECT", "NEEDS_MORE_INFO"}
FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
ALLOWED_CARRIED_WARNING = "historical_duplicates_unchanged_only:new_duplicate_delta_count=0"


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


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _dedupe_preserve(items: Iterable[Any]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for item in items:
        clean = _norm(item)
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _decision_distribution(records: List[Dict[str, Any]]) -> Dict[str, int]:
    distribution: Dict[str, int] = {}
    for record in records:
        decision = _norm(record.get("reviewer_decision")) or PREPARE_DECISION_PENDING
        distribution[decision] = distribution.get(decision, 0) + 1
    return distribution


def _read_workbook_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_excel(path, sheet_name=sheet_name)
    except Exception:
        return pd.DataFrame()
    return df.fillna("")


def load_controlled_official_proposal_human_approval_324k_inputs(
    dry_run_dir: Path,
) -> Dict[str, Any]:
    patch_operations_payload = _read_json(
        dry_run_dir / "controlled_official_proposal_dry_run_324j_patch_operations.json"
    )
    target_diff_payload = _read_json(
        dry_run_dir / "controlled_official_proposal_dry_run_324j_target_asset_diff_preview.json"
    )
    rollback_payload = _read_json(
        dry_run_dir / "controlled_official_proposal_dry_run_324j_rollback_plan.json"
    )
    no_apply_proof = _read_json(
        dry_run_dir / "controlled_official_proposal_dry_run_324j_no_apply_proof.json"
    )
    return {
        "dry_run_summary": _read_json(
            dry_run_dir / "controlled_official_proposal_dry_run_324j_summary.json"
        ),
        "dry_run_qa": _read_json(
            dry_run_dir / "controlled_official_proposal_dry_run_324j_qa.json"
        ),
        "patch_operations_df": pd.DataFrame(
            patch_operations_payload.get("patch_operations", [])
            if isinstance(patch_operations_payload.get("patch_operations", []), list)
            else []
        ).fillna(""),
        "before_after_preview_df": pd.DataFrame(
            target_diff_payload.get("before_after_preview", [])
            if isinstance(target_diff_payload.get("before_after_preview", []), list)
            else []
        ).fillna(""),
        "target_asset_diff_preview_df": pd.DataFrame(
            target_diff_payload.get("target_asset_diff_preview", [])
            if isinstance(target_diff_payload.get("target_asset_diff_preview", []), list)
            else []
        ).fillna(""),
        "rollback_plan_df": pd.DataFrame(
            rollback_payload.get("rollback_plan", [])
            if isinstance(rollback_payload.get("rollback_plan", []), list)
            else []
        ).fillna(""),
        "no_apply_proof_json": no_apply_proof,
    }


def load_controlled_official_proposal_human_approval_324k_reviewed_inputs(
    approval_package_dir: Path,
    reviewed_workbook: Path,
) -> Dict[str, Any]:
    package_json = _read_json(
        approval_package_dir / "controlled_official_proposal_human_approval_324k_package.json"
    )
    return {
        "approval_summary": _read_json(
            approval_package_dir / "controlled_official_proposal_human_approval_324k_summary.json"
        ),
        "approval_qa": _read_json(
            approval_package_dir / "controlled_official_proposal_human_approval_324k_qa.json"
        ),
        "approval_package_json": package_json,
        "reviewed_all_records_df": _read_workbook_sheet(
            reviewed_workbook, "all_approval_records"
        ),
        "reviewed_scope_df": _read_workbook_sheet(reviewed_workbook, "scope_approvals"),
        "reviewed_alias_df": _read_workbook_sheet(reviewed_workbook, "alias_approvals"),
    }


def build_controlled_official_proposal_human_approval_324k_prepare(
    dry_run_summary: Dict[str, Any],
    dry_run_qa: Dict[str, Any],
    patch_operations_df: pd.DataFrame,
    before_after_preview_df: pd.DataFrame,
    target_asset_diff_preview_df: pd.DataFrame,
    rollback_plan_df: pd.DataFrame,
    no_apply_proof_json: Dict[str, Any],
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa(
        "readiness::324j_decision",
        "PASS" if _norm(dry_run_summary.get("decision")) == EXPECTED_324J_DECISION else "FAIL",
        _norm(dry_run_summary.get("decision")),
    )
    add_qa(
        "readiness::324j_qa_fail_count",
        "PASS" if _safe_int(dry_run_summary.get("qa_fail_count")) == 0 else "FAIL",
        str(dry_run_summary.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::324j_qa_json_fail_count",
        "PASS" if _safe_int(dry_run_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(dry_run_qa.get("qa_fail_count", "")),
    )
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
        add_qa(
            f"readiness::324j_{key}",
            "PASS" if _safe_int(dry_run_summary.get(key)) == expected else "FAIL",
            f"expected={expected} actual={dry_run_summary.get(key, '')}",
        )

    carried_warnings = _dedupe_preserve(dry_run_summary.get("carried_warnings", []))
    add_qa(
        "warnings::carried_warning_allowed_only",
        "PASS"
        if not carried_warnings or set(carried_warnings) == {ALLOWED_CARRIED_WARNING}
        else "FAIL",
        " | ".join(carried_warnings),
    )
    if carried_warnings:
        add_qa(
            "warnings::historical_duplicates_unchanged_only",
            "WARN",
            ALLOWED_CARRIED_WARNING,
        )

    no_apply_files_written_to_official_assets = no_apply_proof_json.get(
        "files_written_to_official_assets", []
    )
    add_qa(
        "safety::official_assets_not_written",
        "PASS" if not no_apply_files_written_to_official_assets else "FAIL",
        json.dumps(no_apply_files_written_to_official_assets, ensure_ascii=False),
    )

    operations_df = patch_operations_df.copy().fillna("") if not patch_operations_df.empty else pd.DataFrame()
    add_qa(
        "inputs::patch_operation_count",
        "PASS" if len(operations_df) == 1 else "FAIL",
        f"actual={len(operations_df)}",
    )
    add_qa(
        "inputs::scope_patch_operation_count",
        "PASS"
        if len(operations_df) == 1
        and operations_df["candidate_type"].astype(str).eq("scope_noise").all()
        else "FAIL",
        f"actual={int(operations_df['candidate_type'].astype(str).eq('scope_noise').sum()) if not operations_df.empty else 0}",
    )
    add_qa(
        "inputs::alias_patch_operation_count",
        "PASS"
        if operations_df.empty
        or int(operations_df["candidate_type"].astype(str).eq("alias").sum()) == 0
        else "FAIL",
        f"actual={int(operations_df['candidate_type'].astype(str).eq('alias').sum()) if not operations_df.empty else 0}",
    )

    diff_lookup = (
        {
            _norm(row.get("dry_run_patch_operation_id")): row
            for row in target_asset_diff_preview_df.to_dict(orient="records")
        }
        if not target_asset_diff_preview_df.empty
        else {}
    )
    rollback_lookup = (
        {
            _norm(row.get("dry_run_patch_operation_id")): row
            for row in rollback_plan_df.to_dict(orient="records")
        }
        if not rollback_plan_df.empty
        else {}
    )

    approval_records: List[Dict[str, Any]] = []
    for index, (_, row) in enumerate(operations_df.iterrows(), start=1):
        row_dict = row.to_dict()
        operation_id = _norm(row_dict.get("dry_run_patch_operation_id"))
        diff_row = diff_lookup.get(operation_id, {})
        rollback_row = rollback_lookup.get(operation_id, {})

        approval_records.append(
            {
                "approval_id": f"approval_324k::scope::{index:03d}",
                "reviewer_decision": PREPARE_DECISION_PENDING,
                "reviewer_note": "",
                "reviewer_name": "",
                "approval_timestamp": "",
                "allowed_reviewer_decisions": "APPROVE | REJECT | NEEDS_MORE_INFO",
                "dry_run_patch_operation_id": operation_id,
                "controlled_proposal_id_324i": _norm(row_dict.get("controlled_proposal_id_324i")),
                "source_rule_candidate_id_324h": _norm(
                    row_dict.get("source_rule_candidate_id_324h")
                ),
                "candidate_type": _norm(row_dict.get("candidate_type")),
                "patch_operation_type": _norm(row_dict.get("patch_operation_type")),
                "proposal_type": _norm(row_dict.get("proposal_type")),
                "target_asset_path": _norm(row_dict.get("target_asset_path")),
                "target_group_name": _norm(row_dict.get("target_group_name")),
                "target_locator": _norm(row_dict.get("target_locator")),
                "normalized_label": _norm(row_dict.get("normalized_label")),
                "proposed_change": _norm(row_dict.get("preview_payload_json")),
                "expected_affected_candidate_count": _safe_int(
                    row_dict.get("expected_affected_candidate_count")
                ),
                "expected_trusted_gain": _safe_int(row_dict.get("expected_trusted_gain")),
                "expected_review_reduction": _safe_int(
                    row_dict.get("expected_review_reduction")
                ),
                "expected_out_of_scope_or_rejected_gain": _safe_int(
                    row_dict.get("expected_out_of_scope_or_rejected_gain")
                ),
                "source_candidate_ids_324a": _norm(row_dict.get("source_candidate_ids_324a")),
                "source_review_ids_324b": _norm(row_dict.get("source_review_ids_324b")),
                "source_request_ids_324c": _norm(row_dict.get("source_request_ids_324c")),
                "source_response_ids_324d": _norm(row_dict.get("source_response_ids_324d")),
                "source_validation_ids_324e": _norm(row_dict.get("source_validation_ids_324e")),
                "source_confirmation_ids_324f": _norm(
                    row_dict.get("source_confirmation_ids_324f")
                ),
                "source_sandbox_rule_ids_324g": _norm(
                    row_dict.get("source_sandbox_rule_ids_324g")
                ),
                "provenance": " | ".join(
                    [
                        f"source_candidate_ids_324a={_norm(row_dict.get('source_candidate_ids_324a'))}",
                        f"source_review_ids_324b={_norm(row_dict.get('source_review_ids_324b'))}",
                        f"source_request_ids_324c={_norm(row_dict.get('source_request_ids_324c'))}",
                        f"source_response_ids_324d={_norm(row_dict.get('source_response_ids_324d'))}",
                        f"source_validation_ids_324e={_norm(row_dict.get('source_validation_ids_324e'))}",
                        f"source_confirmation_ids_324f={_norm(row_dict.get('source_confirmation_ids_324f'))}",
                        f"source_sandbox_rule_ids_324g={_norm(row_dict.get('source_sandbox_rule_ids_324g'))}",
                        f"source_rule_candidate_id_324h={_norm(row_dict.get('source_rule_candidate_id_324h'))}",
                    ]
                ),
                "dry_run_evidence": " | ".join(
                    [
                        f"before_state={_norm(diff_row.get('before_state') or row_dict.get('before_state'))}",
                        f"group_before={_norm(diff_row.get('group_before_entry_count') or row_dict.get('group_before_entry_count'))}",
                        f"group_after_preview={_norm(diff_row.get('group_after_entry_count_preview') or row_dict.get('group_after_entry_count_preview'))}",
                        f"official_overlap={_norm(diff_row.get('official_overlap_count') or row_dict.get('already_official_overlap_count'))}",
                        f"target_locator={_norm(row_dict.get('target_locator'))}",
                    ]
                ),
                "rollback_note": _norm(
                    rollback_row.get("rollback_instruction") or row_dict.get("rollback_note")
                ),
                "warning_notes": " | ".join(carried_warnings),
                "risk_flags": _norm(row_dict.get("risk_flags")),
                "proposal_only_no_apply_confirmed": True,
            }
        )

    approvals_df = pd.DataFrame(approval_records).fillna("")
    alias_approvals_df = pd.DataFrame(columns=approvals_df.columns).fillna("")
    scope_approvals_df = approvals_df.copy()
    decision_distribution = _decision_distribution(approval_records)
    duplicate_approval_id_count = (
        int(approvals_df["approval_id"].astype(str).duplicated().sum())
        if not approvals_df.empty
        else 0
    )
    duplicate_patch_operation_id_count = (
        int(approvals_df["dry_run_patch_operation_id"].astype(str).duplicated().sum())
        if not approvals_df.empty
        else 0
    )
    missing_provenance_count = (
        int(approvals_df["provenance"].astype(str).eq("").sum())
        if not approvals_df.empty
        else 0
    )
    missing_rollback_count = (
        int(approvals_df["rollback_note"].astype(str).eq("").sum())
        if not approvals_df.empty
        else 0
    )
    missing_dry_run_evidence_count = (
        int(approvals_df["dry_run_evidence"].astype(str).eq("").sum())
        if not approvals_df.empty
        else 0
    )

    add_qa(
        "approval_counts::approval_record_count",
        "PASS" if len(approval_records) == 1 else "FAIL",
        f"actual={len(approval_records)}",
    )
    add_qa(
        "approval_counts::scope_approval_count",
        "PASS" if len(scope_approvals_df) == 1 else "FAIL",
        f"actual={len(scope_approvals_df)}",
    )
    add_qa(
        "approval_counts::alias_approval_count",
        "PASS" if len(alias_approvals_df) == 0 else "FAIL",
        f"actual={len(alias_approvals_df)}",
    )
    add_qa(
        "approval_integrity::all_pending_human_approval",
        "PASS"
        if not approvals_df.empty
        and approvals_df["reviewer_decision"].astype(str).eq(PREPARE_DECISION_PENDING).all()
        else "FAIL",
        json.dumps(decision_distribution, ensure_ascii=False),
    )
    add_qa(
        "approval_integrity::no_duplicate_approval_id",
        "PASS" if duplicate_approval_id_count == 0 else "FAIL",
        f"actual={duplicate_approval_id_count}",
    )
    add_qa(
        "approval_integrity::no_duplicate_patch_operation_id",
        "PASS" if duplicate_patch_operation_id_count == 0 else "FAIL",
        f"actual={duplicate_patch_operation_id_count}",
    )
    add_qa(
        "approval_integrity::provenance_completeness",
        "PASS" if missing_provenance_count == 0 else "FAIL",
        f"actual={missing_provenance_count}",
    )
    add_qa(
        "approval_integrity::rollback_note_completeness",
        "PASS" if missing_rollback_count == 0 else "FAIL",
        f"actual={missing_rollback_count}",
    )
    add_qa(
        "approval_integrity::dry_run_evidence_completeness",
        "PASS" if missing_dry_run_evidence_count == 0 else "FAIL",
        f"actual={missing_dry_run_evidence_count}",
    )
    add_qa(
        "safety::no_preapproved_records",
        "PASS"
        if approvals_df.empty
        or approvals_df["reviewer_decision"].astype(str).eq(PREPARE_DECISION_PENDING).all()
        else "FAIL",
        "all records remain pending",
    )
    add_qa(
        "safety::no_official_file_modification",
        "PASS",
        "324K prepares approval records only and does not modify official assets.",
    )
    add_qa(
        "safety::no_llm_or_api_call_executed",
        "PASS",
        "324K uses 324J dry-run output only.",
    )

    review_instructions_df = pd.DataFrame(
        [
            {
                "section": "package_purpose",
                "instruction": "Review the single 324J dry-run scope patch operation and decide whether it should proceed to later official patch application.",
            },
            {
                "section": "allowed_decisions",
                "instruction": "Allowed reviewer_decision values: APPROVE, REJECT, NEEDS_MORE_INFO.",
            },
            {
                "section": "approval_rule",
                "instruction": "Approve only when target asset/group, proposed change, provenance, dry-run evidence, rollback note, and warning notes all look safe and correct.",
            },
            {
                "section": "blocking_rule",
                "instruction": "Use NEEDS_MORE_INFO whenever provenance, semantics, or safety assumptions are incomplete for a safe official patch decision.",
            },
            {
                "section": "no_apply_note",
                "instruction": "324K does not apply any patch and does not modify official mapping, override, or production pipeline files.",
            },
        ]
    ).fillna("")

    no_apply_proof_df = pd.DataFrame(
        [
            {
                "files_read_count": len(no_apply_proof_json.get("files_read", [])),
                "files_written_count": len(no_apply_proof_json.get("files_written", [])),
                "official_target_files_inspected_count": len(
                    no_apply_proof_json.get("target_official_files_inspected", [])
                ),
                "official_target_files_not_modified_count": len(
                    no_apply_proof_json.get("official_assets_not_modified", [])
                ),
                "files_written_to_official_assets_count": len(
                    no_apply_files_written_to_official_assets
                ),
                "output_only_write_confirmation": bool(
                    no_apply_proof_json.get("output_only_write_confirmation", False)
                ),
                "decision": _norm(no_apply_proof_json.get("decision")),
            }
        ]
    ).fillna("")

    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "approval_only",
                "detail": "324K creates a human approval package only and does not modify official assets.",
            },
            {
                "limitation": "single_scope_patch_only",
                "detail": "324K processes only the single 324J dry-run scope patch operation.",
            },
            {
                "limitation": "later_patch_stage_required",
                "detail": "Even an APPROVE decision here only prepares for a later official patch application stage.",
            },
        ]
    )

    qa_checks_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_checks_df["status"] == "PASS").sum()) if not qa_checks_df.empty else 0
    qa_warn_count = int((qa_checks_df["status"] == "WARN").sum()) if not qa_checks_df.empty else 0
    qa_fail_count = int((qa_checks_df["status"] == "FAIL").sum()) if not qa_checks_df.empty else 0
    blocking_reasons = (
        qa_checks_df.loc[qa_checks_df["status"] == "FAIL", "check_name"]
        .astype(str)
        .tolist()
        if not qa_checks_df.empty
        else []
    )

    summary = {
        "stage": "324K",
        "mode": "prepare",
        "output_dir": "",
        "source_dry_run_decision": _norm(dry_run_summary.get("decision")),
        "source_dry_run_qa_fail_count": _safe_int(dry_run_summary.get("qa_fail_count")),
        "approval_record_count": len(approval_records),
        "alias_approval_count": len(alias_approvals_df),
        "scope_approval_count": len(scope_approvals_df),
        "pending_count": int(
            approvals_df["reviewer_decision"].astype(str).eq(PREPARE_DECISION_PENDING).sum()
        )
        if not approvals_df.empty
        else 0,
        "approved_count": 0,
        "rejected_count": 0,
        "needs_more_info_count": 0,
        "decision_distribution": decision_distribution,
        "carried_warnings": carried_warnings,
        "expected_affected_candidate_count": int(
            approvals_df["expected_affected_candidate_count"].sum()
        )
        if not approvals_df.empty
        else 0,
        "expected_trusted_gain": int(approvals_df["expected_trusted_gain"].sum())
        if not approvals_df.empty
        else 0,
        "expected_review_reduction": int(
            approvals_df["expected_review_reduction"].sum()
        )
        if not approvals_df.empty
        else 0,
        "expected_out_of_scope_or_rejected_gain": int(
            approvals_df["expected_out_of_scope_or_rejected_gain"].sum()
        )
        if not approvals_df.empty
        else 0,
        "official_assets_not_modified_confirmed": True,
        "approval_package_only_no_apply_confirmed": True,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": PREPARE_READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION,
    }

    approval_package_json = {
        "stage": "324K",
        "mode": "prepare",
        "decision": summary["decision"],
        "allowed_reviewer_decisions": sorted(ALLOWED_REVIEWER_DECISIONS),
        "approval_records": approval_records,
        "alias_approval_records": [],
        "scope_approval_records": scope_approvals_df.to_dict(orient="records"),
    }
    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_checks_df.to_dict(orient="records"),
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

    notes_markdown = "\n".join(
        [
            "# Controlled Official Proposal Human Approval 324K",
            "",
            "## Decision",
            f"- {summary.get('decision', '')}",
            "",
            "## Approval Counts",
            f"- approval_record_count: {summary.get('approval_record_count', 0)}",
            f"- alias_approval_count: {summary.get('alias_approval_count', 0)}",
            f"- scope_approval_count: {summary.get('scope_approval_count', 0)}",
            f"- pending_count: {summary.get('pending_count', 0)}",
            "",
            "## Notes",
            "- 324K is a human approval package only.",
            "- The single approval record remains pending until a human reviewer updates the workbook.",
            "- No official asset or production pipeline file is modified in this stage.",
            "",
        ]
    )

    return {
        "summary": summary,
        "approval_records_df": approvals_df,
        "alias_approvals_df": alias_approvals_df,
        "scope_approvals_df": scope_approvals_df,
        "before_after_preview_df": before_after_preview_df,
        "rollback_plan_df": rollback_plan_df,
        "review_instructions_df": review_instructions_df,
        "no_apply_proof_df": no_apply_proof_df,
        "known_limitations_df": known_limitations_df,
        "qa_summary_df": qa_summary_df,
        "qa_checks_df": qa_checks_df,
        "approval_package_json": approval_package_json,
        "qa_json": qa_json,
        "no_apply_proof_json": no_apply_proof_json,
        "notes_markdown": notes_markdown,
    }


def _normalize_reviewer_decision(value: Any) -> str:
    return _norm(value).upper()


def build_controlled_official_proposal_human_approval_324k_validate_reviewed(
    approval_summary: Dict[str, Any],
    approval_qa: Dict[str, Any],
    approval_package_json: Dict[str, Any],
    reviewed_all_records_df: pd.DataFrame,
    reviewed_scope_df: pd.DataFrame,
    reviewed_alias_df: pd.DataFrame,
    reviewed_workbook: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa(
        "readiness::324k_decision",
        "PASS" if _norm(approval_summary.get("decision")) == PREPARE_READY_DECISION else "FAIL",
        _norm(approval_summary.get("decision")),
    )
    add_qa(
        "readiness::324k_qa_fail_count",
        "PASS" if _safe_int(approval_summary.get("qa_fail_count")) == 0 else "FAIL",
        str(approval_summary.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::324k_qa_json_fail_count",
        "PASS" if _safe_int(approval_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(approval_qa.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::324k_approval_record_count",
        "PASS" if _safe_int(approval_summary.get("approval_record_count")) == 1 else "FAIL",
        str(approval_summary.get("approval_record_count", "")),
    )

    all_records_df = reviewed_all_records_df.copy().fillna("")
    if all_records_df.empty:
        all_records_df = pd.concat(
            [reviewed_scope_df.copy().fillna(""), reviewed_alias_df.copy().fillna("")],
            ignore_index=True,
        ).fillna("")

    required_columns = {
        "approval_id",
        "reviewer_decision",
        "reviewer_note",
        "reviewer_name",
        "approval_timestamp",
        "dry_run_patch_operation_id",
        "controlled_proposal_id_324i",
        "source_rule_candidate_id_324h",
        "target_asset_path",
        "target_group_name",
        "proposed_change",
        "provenance",
        "dry_run_evidence",
        "rollback_note",
    }
    missing_columns = sorted(required_columns.difference(set(all_records_df.columns)))
    add_qa(
        "reviewed_integrity::required_columns_present",
        "PASS" if not missing_columns else "FAIL",
        "none" if not missing_columns else " | ".join(missing_columns),
    )

    add_qa(
        "reviewed_counts::approval_record_count",
        "PASS" if len(all_records_df) == 1 else "FAIL",
        f"actual={len(all_records_df)}",
    )
    add_qa(
        "reviewed_counts::scope_approval_record_count",
        "PASS"
        if int(all_records_df["candidate_type"].astype(str).eq("scope_noise").sum()) == 1
        else "FAIL",
        f"actual={int(all_records_df['candidate_type'].astype(str).eq('scope_noise').sum()) if not all_records_df.empty else 0}",
    )

    package_records = approval_package_json.get("approval_records", [])
    package_df = pd.DataFrame(package_records if isinstance(package_records, list) else []).fillna("")
    package_approval_ids = set(package_df.get("approval_id", pd.Series(dtype=str)).astype(str))
    reviewed_approval_ids = set(
        all_records_df.get("approval_id", pd.Series(dtype=str)).astype(str)
    )
    add_qa(
        "reviewed_integrity::approval_ids_match_package",
        "PASS" if reviewed_approval_ids == package_approval_ids else "FAIL",
        f"package={len(package_approval_ids)} reviewed={len(reviewed_approval_ids)}",
    )

    normalized_df = all_records_df.copy().fillna("")
    if not normalized_df.empty:
        normalized_df["reviewer_decision_normalized"] = normalized_df["reviewer_decision"].map(
            _normalize_reviewer_decision
        )

    pending_count = 0
    invalid_decision_count = 0
    for row in normalized_df.to_dict(orient="records") if not normalized_df.empty else []:
        decision = _normalize_reviewer_decision(row.get("reviewer_decision"))
        if decision in {"", PREPARE_DECISION_PENDING}:
            pending_count += 1
        elif decision not in ALLOWED_REVIEWER_DECISIONS:
            invalid_decision_count += 1

    add_qa(
        "reviewed_integrity::no_pending_decisions",
        "PASS" if pending_count == 0 else "FAIL",
        f"actual={pending_count}",
    )
    add_qa(
        "reviewed_integrity::no_invalid_decisions",
        "PASS" if invalid_decision_count == 0 else "FAIL",
        f"actual={invalid_decision_count}",
    )

    approved_df = (
        normalized_df.loc[
            normalized_df["reviewer_decision_normalized"].astype(str) == "APPROVE"
        ].copy()
        if not normalized_df.empty
        else pd.DataFrame()
    )
    rejected_df = (
        normalized_df.loc[
            normalized_df["reviewer_decision_normalized"].astype(str) == "REJECT"
        ].copy()
        if not normalized_df.empty
        else pd.DataFrame()
    )
    needs_more_info_df = (
        normalized_df.loc[
            normalized_df["reviewer_decision_normalized"].astype(str) == "NEEDS_MORE_INFO"
        ].copy()
        if not normalized_df.empty
        else pd.DataFrame()
    )

    if len(approved_df) == 1 and len(rejected_df) == 0 and len(needs_more_info_df) == 0:
        final_decision = REVIEWED_APPROVED_DECISION
    elif len(rejected_df) == 1 and len(approved_df) == 0 and len(needs_more_info_df) == 0:
        final_decision = REVIEWED_REJECTED_DECISION
    elif len(needs_more_info_df) == 1 and len(approved_df) == 0 and len(rejected_df) == 0:
        final_decision = REVIEWED_NEEDS_INFO_DECISION
    else:
        final_decision = NOT_READY_DECISION

    add_qa(
        "reviewed_counts::approved_count",
        "PASS" if len(approved_df) in {0, 1} else "FAIL",
        f"actual={len(approved_df)}",
    )
    add_qa(
        "reviewed_counts::rejected_count",
        "PASS" if len(rejected_df) in {0, 1} else "FAIL",
        f"actual={len(rejected_df)}",
    )
    add_qa(
        "reviewed_counts::needs_more_info_count",
        "PASS" if len(needs_more_info_df) in {0, 1} else "FAIL",
        f"actual={len(needs_more_info_df)}",
    )
    add_qa(
        "safety::no_official_file_modification",
        "PASS",
        "324K reviewed validation only checks the workbook and does not modify official assets.",
    )
    add_qa(
        "safety::no_llm_or_api_call_executed",
        "PASS",
        "324K reviewed validation uses the 324K package and reviewed workbook only.",
    )

    qa_checks_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_checks_df["status"] == "PASS").sum()) if not qa_checks_df.empty else 0
    qa_warn_count = int((qa_checks_df["status"] == "WARN").sum()) if not qa_checks_df.empty else 0
    qa_fail_count = int((qa_checks_df["status"] == "FAIL").sum()) if not qa_checks_df.empty else 0
    blocking_reasons = (
        qa_checks_df.loc[qa_checks_df["status"] == "FAIL", "check_name"]
        .astype(str)
        .tolist()
        if not qa_checks_df.empty
        else []
    )

    decision_distribution = _decision_distribution(
        normalized_df.drop(columns=["reviewer_decision_normalized"], errors="ignore").to_dict(
            orient="records"
        )
        if not normalized_df.empty
        else []
    )
    summary = {
        "stage": "324K-R",
        "mode": "validate-reviewed",
        "output_dir": "",
        "reviewed_workbook_path": str(reviewed_workbook),
        "source_approval_package_decision": _norm(approval_summary.get("decision")),
        "source_approval_package_qa_fail_count": _safe_int(approval_summary.get("qa_fail_count")),
        "approval_record_count": len(normalized_df),
        "approved_count": len(approved_df),
        "rejected_count": len(rejected_df),
        "needs_more_info_count": len(needs_more_info_df),
        "pending_count": pending_count,
        "invalid_decision_count": invalid_decision_count,
        "decision_distribution": decision_distribution,
        "official_assets_not_modified_confirmed": True,
        "approval_package_only_no_apply_confirmed": True,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": final_decision if qa_fail_count == 0 else NOT_READY_DECISION,
    }

    final_review_result_json = {
        "stage": "324K-R",
        "mode": "validate-reviewed",
        "decision": summary["decision"],
        "reviewed_workbook_path": str(reviewed_workbook),
        "approved_records": approved_df.drop(
            columns=["reviewer_decision_normalized"], errors="ignore"
        ).to_dict(orient="records"),
        "rejected_records": rejected_df.drop(
            columns=["reviewer_decision_normalized"], errors="ignore"
        ).to_dict(orient="records"),
        "needs_more_info_records": needs_more_info_df.drop(
            columns=["reviewer_decision_normalized"], errors="ignore"
        ).to_dict(orient="records"),
    }
    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_checks_df.to_dict(orient="records"),
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

    notes_markdown = "\n".join(
        [
            "# Controlled Official Proposal Human Approval 324K Reviewed",
            "",
            "## Decision",
            f"- {summary.get('decision', '')}",
            "",
            "## Reviewed Counts",
            f"- approval_record_count: {summary.get('approval_record_count', 0)}",
            f"- approved_count: {summary.get('approved_count', 0)}",
            f"- rejected_count: {summary.get('rejected_count', 0)}",
            f"- needs_more_info_count: {summary.get('needs_more_info_count', 0)}",
            f"- pending_count: {summary.get('pending_count', 0)}",
            f"- invalid_decision_count: {summary.get('invalid_decision_count', 0)}",
            "",
        ]
    )

    return {
        "summary": summary,
        "approved_df": approved_df.drop(
            columns=["reviewer_decision_normalized"], errors="ignore"
        ),
        "rejected_df": rejected_df.drop(
            columns=["reviewer_decision_normalized"], errors="ignore"
        ),
        "needs_more_info_df": needs_more_info_df.drop(
            columns=["reviewer_decision_normalized"], errors="ignore"
        ),
        "all_reviewed_df": normalized_df.drop(
            columns=["reviewer_decision_normalized"], errors="ignore"
        ),
        "qa_summary_df": qa_summary_df,
        "qa_checks_df": qa_checks_df,
        "qa_json": qa_json,
        "final_review_result_json": final_review_result_json,
        "notes_markdown": notes_markdown,
    }
