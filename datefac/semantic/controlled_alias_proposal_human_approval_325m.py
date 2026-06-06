from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

import pandas as pd


EXPECTED_325L_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_DRY_RUN_325L_READY_FOR_HUMAN_APPROVAL"
PREPARE_READY_DECISION = "CONTROLLED_ALIAS_PROPOSAL_HUMAN_APPROVAL_325M_READY_FOR_HUMAN_REVIEW"
REVIEWED_APPROVED_DECISION = (
    "CONTROLLED_ALIAS_PROPOSAL_HUMAN_APPROVAL_325M_REVIEWED_READY_FOR_325N_OFFICIAL_PATCH_APPLICATION"
)
REVIEWED_NO_APPROVED_DECISION = (
    "CONTROLLED_ALIAS_PROPOSAL_HUMAN_APPROVAL_325M_REVIEWED_NO_APPROVED_PATCH_OPERATIONS"
)
REVIEWED_NOT_READY_DECISION = "CONTROLLED_ALIAS_PROPOSAL_HUMAN_APPROVAL_325M_REVIEWED_NOT_READY"
NOT_READY_DECISION = "CONTROLLED_ALIAS_PROPOSAL_HUMAN_APPROVAL_325M_NOT_READY"

DEFAULT_OUTPUT_DIR = Path(
    r"D:\_datefac\output\controlled_alias_proposal_human_approval_325m"
)
DEFAULT_REVIEWED_OUTPUT_DIR = Path(
    r"D:\_datefac\output\controlled_alias_proposal_human_approval_325m_reviewed"
)

PREPARE_DECISION_PENDING = "PENDING_HUMAN_APPROVAL"
ALLOWED_REVIEWER_DECISIONS = {"APPROVE", "REJECT", "NEEDS_MORE_INFO"}
OFFICIAL_ALIAS_ASSET_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")
FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")


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


def _decision_distribution(records: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    distribution: Dict[str, int] = {}
    for record in records:
        decision = _norm(record.get(key)) or PREPARE_DECISION_PENDING
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


def load_controlled_alias_proposal_human_approval_325m_inputs(
    dry_run_dir: Path,
) -> Dict[str, Any]:
    patch_operations_payload = _read_json(
        dry_run_dir / "controlled_official_proposal_dry_run_325l_patch_operations.json"
    )
    target_diff_payload = _read_json(
        dry_run_dir / "controlled_official_proposal_dry_run_325l_target_asset_diff_preview.json"
    )
    rollback_payload = _read_json(
        dry_run_dir / "controlled_official_proposal_dry_run_325l_rollback_plan.json"
    )
    no_apply_proof = _read_json(
        dry_run_dir / "controlled_official_proposal_dry_run_325l_no_apply_proof.json"
    )
    return {
        "dry_run_summary": _read_json(
            dry_run_dir / "controlled_official_proposal_dry_run_325l_summary.json"
        ),
        "dry_run_qa": _read_json(
            dry_run_dir / "controlled_official_proposal_dry_run_325l_qa.json"
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


def load_controlled_alias_proposal_human_approval_325m_reviewed_inputs(
    approval_package_dir: Path,
    reviewed_workbook: Path,
) -> Dict[str, Any]:
    package_json = _read_json(
        approval_package_dir / "controlled_alias_proposal_human_approval_325m_package.json"
    )
    return {
        "approval_summary": _read_json(
            approval_package_dir / "controlled_alias_proposal_human_approval_325m_summary.json"
        ),
        "approval_qa": _read_json(
            approval_package_dir / "controlled_alias_proposal_human_approval_325m_qa.json"
        ),
        "approval_package_json": package_json,
        "reviewed_all_records_df": _read_workbook_sheet(
            reviewed_workbook, "all_approval_records"
        ),
        "reviewed_alias_df": _read_workbook_sheet(reviewed_workbook, "alias_approvals"),
        "reviewed_scope_df": _read_workbook_sheet(reviewed_workbook, "scope_approvals"),
    }


def build_controlled_alias_proposal_human_approval_325m_prepare(
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

    readiness_checks = [
        ("decision", EXPECTED_325L_DECISION),
        ("qa_fail_count", 0),
        ("proposal_count", 6),
        ("patch_operation_count", 6),
        ("alias_patch_operation_count", 6),
        ("scope_patch_operation_count", 0),
        ("target_asset_file_count", 1),
        ("target_asset_plan_count", 6),
        ("duplicate_operation_count", 0),
        ("duplicate_alias_target_pair_count", 0),
        ("target_conflict_count", 0),
        ("already_official_overlap_count", 0),
        ("missing_target_asset_or_group_count", 0),
        ("missing_provenance_count", 0),
        ("adjusted_metric_mismatch_count", 0),
        ("diluted_eps_mismatch_count", 0),
    ]
    for key, expected in readiness_checks:
        actual = dry_run_summary.get(key)
        ok = _safe_int(actual) == expected if isinstance(expected, int) else _norm(actual) == expected
        add_qa(f"readiness::325l_{key}", "PASS" if ok else "FAIL", f"expected={expected}; actual={actual}")

    add_qa(
        "readiness::325l_official_asset_hash_unchanged",
        "PASS" if bool(dry_run_summary.get("official_asset_hash_unchanged")) else "FAIL",
        str(dry_run_summary.get("official_asset_hash_unchanged")),
    )
    files_written_to_official_assets = dry_run_summary.get("files_written_to_official_assets", [])
    add_qa(
        "readiness::325l_files_written_to_official_assets_empty",
        "PASS" if not files_written_to_official_assets else "FAIL",
        json.dumps(files_written_to_official_assets, ensure_ascii=False),
    )
    add_qa(
        "readiness::325l_qa_json_fail_count",
        "PASS" if _safe_int(dry_run_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(dry_run_qa.get("qa_fail_count", "")),
    )

    operations_df = patch_operations_df.copy().fillna("") if not patch_operations_df.empty else pd.DataFrame()
    add_qa(
        "inputs::loaded_patch_operation_count",
        "PASS" if len(operations_df) == 6 else "FAIL",
        f"actual={len(operations_df)}",
    )
    add_qa(
        "inputs::loaded_alias_patch_operation_count",
        "PASS"
        if len(operations_df) == 6
        and int(operations_df["candidate_type"].astype(str).eq("alias").sum()) == 6
        else "FAIL",
        f"actual={int(operations_df['candidate_type'].astype(str).eq('alias').sum()) if not operations_df.empty else 0}",
    )
    add_qa(
        "inputs::loaded_scope_patch_operation_count",
        "PASS"
        if operations_df.empty
        or int(operations_df["candidate_type"].astype(str).eq("scope").sum()) == 0
        else "FAIL",
        f"actual={int(operations_df['candidate_type'].astype(str).eq('scope').sum()) if not operations_df.empty else 0}",
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
        safety_checks = {
            "target_group_exists": bool(row_dict.get("target_group_exists")),
            "already_official_overlap_count": _safe_int(row_dict.get("already_official_overlap_count")),
            "target_conflict_count": _safe_int(row_dict.get("target_conflict_count")),
            "before_state": _norm(row_dict.get("before_state")),
            "confidence": _norm(row_dict.get("confidence")),
        }
        semantic_summary = {
            "semantic_constraint_pass": bool(row_dict.get("semantic_constraint_pass")),
            "adjusted_metric_mismatch": bool(row_dict.get("adjusted_metric_mismatch")),
            "diluted_eps_mismatch": bool(row_dict.get("diluted_eps_mismatch")),
            "semantic_constraint_failures": _norm(row_dict.get("semantic_constraint_failures")),
        }
        provenance = {
            "source_candidate_id_325a": _norm(row_dict.get("source_candidate_id_325a")),
            "source_candidate_id_325j": _norm(row_dict.get("source_candidate_id_325j")),
            "source_sandbox_rule_id_325i": _norm(row_dict.get("source_sandbox_rule_id_325i")),
            "source_confirmation_id_325h": _norm(row_dict.get("source_confirmation_id_325h")),
            "source_request_id_325e": _norm(row_dict.get("source_request_id_325e")),
            "controlled_proposal_id_325k": _norm(row_dict.get("controlled_proposal_id_325k")),
        }
        approval_records.append(
            {
                "approval_record_id": f"approval_325m::alias::{index:03d}",
                "patch_operation_id": operation_id,
                "proposal_id": _norm(row_dict.get("controlled_proposal_id_325k")),
                "candidate_id": _norm(row_dict.get("source_candidate_id_325j")),
                "operation": _norm(row_dict.get("operation")),
                "candidate_type": _norm(row_dict.get("candidate_type")),
                "alias_label": _norm(row_dict.get("alias_label")),
                "normalized_alias_label": _norm(row_dict.get("normalized_alias_label")),
                "target_metric": _norm(row_dict.get("target_metric")),
                "target_asset_file": _norm(row_dict.get("target_asset_file")),
                "target_asset_group": _norm(row_dict.get("target_asset_group")),
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
                "safety_checks": json.dumps(safety_checks, ensure_ascii=False),
                "semantic_constraint_summary": json.dumps(semantic_summary, ensure_ascii=False),
                "dry_run_diff_preview": json.dumps(
                    {
                        "before_state": _norm(diff_row.get("before_state")),
                        "group_before_entry_count": _safe_int(
                            diff_row.get("group_before_entry_count")
                        ),
                        "group_after_entry_count_preview": _safe_int(
                            diff_row.get("group_after_entry_count_preview")
                        ),
                        "virtual_diff_summary": _norm(diff_row.get("virtual_diff_summary")),
                    },
                    ensure_ascii=False,
                ),
                "rollback_reference": json.dumps(
                    {
                        "rollback_action": _norm(rollback_row.get("rollback_action")),
                        "rollback_instruction": _norm(
                            rollback_row.get("rollback_instruction")
                        ),
                        "rollback_reason": _norm(rollback_row.get("rollback_reason")),
                    },
                    ensure_ascii=False,
                ),
                "provenance": json.dumps(provenance, ensure_ascii=False),
                "human_approval_decision": PREPARE_DECISION_PENDING,
                "reviewer_name": "",
                "reviewer_note": "",
                "review_timestamp": "",
                "allowed_human_approval_decisions": "APPROVE | REJECT | NEEDS_MORE_INFO",
            }
        )

    approvals_df = pd.DataFrame(approval_records).fillna("")
    alias_approvals_df = approvals_df.copy()
    scope_approvals_df = pd.DataFrame(columns=approvals_df.columns).fillna("")

    decision_distribution = _decision_distribution(
        approval_records, key="human_approval_decision"
    )
    duplicate_approval_id_count = (
        int(approvals_df["approval_record_id"].astype(str).duplicated().sum())
        if not approvals_df.empty
        else 0
    )
    duplicate_patch_operation_id_count = (
        int(approvals_df["patch_operation_id"].astype(str).duplicated().sum())
        if not approvals_df.empty
        else 0
    )
    missing_provenance_count = (
        int(approvals_df["provenance"].astype(str).eq("").sum())
        if not approvals_df.empty
        else 0
    )
    missing_rollback_reference_count = (
        int(approvals_df["rollback_reference"].astype(str).eq("").sum())
        if not approvals_df.empty
        else 0
    )
    missing_diff_preview_count = (
        int(approvals_df["dry_run_diff_preview"].astype(str).eq("").sum())
        if not approvals_df.empty
        else 0
    )

    add_qa(
        "approval_counts::approval_record_count",
        "PASS" if len(approval_records) == 6 else "FAIL",
        f"actual={len(approval_records)}",
    )
    add_qa(
        "approval_counts::alias_approval_count",
        "PASS" if len(alias_approvals_df) == 6 else "FAIL",
        f"actual={len(alias_approvals_df)}",
    )
    add_qa(
        "approval_counts::scope_approval_count",
        "PASS" if len(scope_approvals_df) == 0 else "FAIL",
        f"actual={len(scope_approvals_df)}",
    )
    add_qa(
        "approval_integrity::all_pending_human_approval",
        "PASS"
        if not approvals_df.empty
        and approvals_df["human_approval_decision"].astype(str).eq(PREPARE_DECISION_PENDING).all()
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
        "approval_integrity::rollback_reference_completeness",
        "PASS" if missing_rollback_reference_count == 0 else "FAIL",
        f"actual={missing_rollback_reference_count}",
    )
    add_qa(
        "approval_integrity::dry_run_diff_preview_completeness",
        "PASS" if missing_diff_preview_count == 0 else "FAIL",
        f"actual={missing_diff_preview_count}",
    )

    files_written_to_official_assets = no_apply_proof_json.get("files_written_to_official_assets", [])
    add_qa(
        "safety::official_assets_not_written",
        "PASS" if not files_written_to_official_assets else "FAIL",
        json.dumps(files_written_to_official_assets, ensure_ascii=False),
    )
    add_qa(
        "safety::no_official_file_modification",
        "PASS",
        "325M prepares approval records only and does not modify official assets.",
    )
    add_qa(
        "safety::no_llm_or_api_call_executed",
        "PASS",
        "325M uses 325L dry-run output only.",
    )

    review_instructions_df = pd.DataFrame(
        [
            {
                "section": "package_purpose",
                "instruction": "Review the 6 alias dry-run patch operations and decide which ones may proceed to later official patch application.",
            },
            {
                "section": "allowed_decisions",
                "instruction": "Allowed human_approval_decision values: APPROVE, REJECT, NEEDS_MORE_INFO.",
            },
            {
                "section": "approval_rule",
                "instruction": "Approve only when alias label, target metric, safety checks, semantic constraint summary, diff preview, rollback reference, and provenance all look safe and correct.",
            },
            {
                "section": "blocking_rule",
                "instruction": "Use NEEDS_MORE_INFO whenever semantics, provenance, or safety assumptions are incomplete for a safe official patch decision.",
            },
            {
                "section": "no_apply_note",
                "instruction": "325M does not apply any patch and does not modify official mapping, override, or production pipeline files.",
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
                    files_written_to_official_assets
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
                "detail": "325M creates a human approval package only and does not modify official assets.",
            },
            {
                "limitation": "alias_patch_operations_only",
                "detail": "325M processes only the 6 alias dry-run patch operations from 325L.",
            },
            {
                "limitation": "later_patch_stage_required",
                "detail": "Even an APPROVE decision here only prepares for a later official patch application stage.",
            },
        ]
    ).fillna("")

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
        "stage": "325M",
        "mode": "prepare",
        "output_dir": "",
        "source_dry_run_decision": _norm(dry_run_summary.get("decision")),
        "source_dry_run_qa_fail_count": _safe_int(dry_run_summary.get("qa_fail_count")),
        "approval_record_count": len(approval_records),
        "alias_approval_count": len(alias_approvals_df),
        "scope_approval_count": len(scope_approvals_df),
        "pending_count": int(
            approvals_df["human_approval_decision"].astype(str).eq(PREPARE_DECISION_PENDING).sum()
        )
        if not approvals_df.empty
        else 0,
        "approved_count": 0,
        "rejected_count": 0,
        "needs_more_info_count": 0,
        "decision_distribution": decision_distribution,
        "expected_affected_candidate_count": int(
            pd.to_numeric(approvals_df["expected_affected_candidate_count"], errors="coerce").fillna(0).sum()
        )
        if not approvals_df.empty
        else 0,
        "expected_trusted_gain": int(
            pd.to_numeric(approvals_df["expected_trusted_gain"], errors="coerce").fillna(0).sum()
        )
        if not approvals_df.empty
        else 0,
        "expected_review_reduction": int(
            pd.to_numeric(approvals_df["expected_review_reduction"], errors="coerce").fillna(0).sum()
        )
        if not approvals_df.empty
        else 0,
        "expected_out_of_scope_or_rejected_gain": int(
            pd.to_numeric(
                approvals_df["expected_out_of_scope_or_rejected_gain"], errors="coerce"
            )
            .fillna(0)
            .sum()
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
        "stage": "325M",
        "mode": "prepare",
        "decision": summary["decision"],
        "allowed_human_approval_decisions": sorted(ALLOWED_REVIEWER_DECISIONS),
        "approval_records": approval_records,
        "alias_approval_records": alias_approvals_df.to_dict(orient="records"),
        "scope_approval_records": [],
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
            "# Controlled Alias Proposal Human Approval 325M",
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
            "- 325M is a human approval package only.",
            "- The 6 approval records remain pending until a human reviewer updates the workbook.",
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


def build_controlled_alias_proposal_human_approval_325m_validate_reviewed(
    approval_summary: Dict[str, Any],
    approval_qa: Dict[str, Any],
    approval_package_json: Dict[str, Any],
    reviewed_all_records_df: pd.DataFrame,
    reviewed_alias_df: pd.DataFrame,
    reviewed_scope_df: pd.DataFrame,
    reviewed_workbook: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa(
        "readiness::325m_decision",
        "PASS" if _norm(approval_summary.get("decision")) == PREPARE_READY_DECISION else "FAIL",
        _norm(approval_summary.get("decision")),
    )
    add_qa(
        "readiness::325m_qa_fail_count",
        "PASS" if _safe_int(approval_summary.get("qa_fail_count")) == 0 else "FAIL",
        str(approval_summary.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::325m_qa_json_fail_count",
        "PASS" if _safe_int(approval_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(approval_qa.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::325m_approval_record_count",
        "PASS" if _safe_int(approval_summary.get("approval_record_count")) == 6 else "FAIL",
        str(approval_summary.get("approval_record_count", "")),
    )

    all_records_df = reviewed_all_records_df.copy().fillna("")
    if all_records_df.empty:
        all_records_df = pd.concat(
            [reviewed_alias_df.copy().fillna(""), reviewed_scope_df.copy().fillna("")],
            ignore_index=True,
        ).fillna("")

    required_columns = {
        "approval_record_id",
        "patch_operation_id",
        "proposal_id",
        "candidate_id",
        "operation",
        "alias_label",
        "normalized_alias_label",
        "target_metric",
        "target_asset_file",
        "target_asset_group",
        "safety_checks",
        "semantic_constraint_summary",
        "dry_run_diff_preview",
        "rollback_reference",
        "provenance",
        "human_approval_decision",
        "reviewer_name",
        "reviewer_note",
        "review_timestamp",
    }
    missing_columns = sorted(required_columns.difference(set(all_records_df.columns)))
    add_qa(
        "reviewed_integrity::required_columns_present",
        "PASS" if not missing_columns else "FAIL",
        "none" if not missing_columns else " | ".join(missing_columns),
    )

    add_qa(
        "reviewed_counts::approval_record_count",
        "PASS" if len(all_records_df) == 6 else "FAIL",
        f"actual={len(all_records_df)}",
    )
    add_qa(
        "reviewed_counts::alias_approval_record_count",
        "PASS"
        if int(all_records_df["target_asset_file"].astype(str).eq("data/overrides/semantic_alias_candidates.json").sum()) == 6
        else "FAIL",
        f"actual={int(all_records_df['target_asset_file'].astype(str).eq('data/overrides/semantic_alias_candidates.json').sum()) if not all_records_df.empty else 0}",
    )
    add_qa(
        "reviewed_counts::scope_approval_record_count",
        "PASS"
        if reviewed_scope_df.empty or len(reviewed_scope_df) == 0
        else "FAIL",
        f"actual={len(reviewed_scope_df)}",
    )

    package_records = approval_package_json.get("approval_records", [])
    package_df = pd.DataFrame(package_records if isinstance(package_records, list) else []).fillna("")
    package_approval_ids = set(package_df.get("approval_record_id", pd.Series(dtype=str)).astype(str))
    reviewed_approval_ids = set(
        all_records_df.get("approval_record_id", pd.Series(dtype=str)).astype(str)
    )
    add_qa(
        "reviewed_integrity::approval_ids_match_package",
        "PASS" if reviewed_approval_ids == package_approval_ids else "FAIL",
        f"package={len(package_approval_ids)} reviewed={len(reviewed_approval_ids)}",
    )

    normalized_df = all_records_df.copy().fillna("")
    if not normalized_df.empty:
        normalized_df["human_approval_decision_normalized"] = normalized_df["human_approval_decision"].map(
            _normalize_reviewer_decision
        )

    pending_count = 0
    invalid_decision_count = 0
    for row in normalized_df.to_dict(orient="records") if not normalized_df.empty else []:
        decision = _normalize_reviewer_decision(row.get("human_approval_decision"))
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
            normalized_df["human_approval_decision_normalized"].astype(str) == "APPROVE"
        ].copy()
        if not normalized_df.empty
        else pd.DataFrame()
    )
    rejected_df = (
        normalized_df.loc[
            normalized_df["human_approval_decision_normalized"].astype(str) == "REJECT"
        ].copy()
        if not normalized_df.empty
        else pd.DataFrame()
    )
    needs_more_info_df = (
        normalized_df.loc[
            normalized_df["human_approval_decision_normalized"].astype(str)
            == "NEEDS_MORE_INFO"
        ].copy()
        if not normalized_df.empty
        else pd.DataFrame()
    )

    if pending_count > 0 or invalid_decision_count > 0:
        final_decision = REVIEWED_NOT_READY_DECISION
    elif len(approved_df) > 0:
        final_decision = REVIEWED_APPROVED_DECISION
    else:
        final_decision = REVIEWED_NO_APPROVED_DECISION

    add_qa(
        "reviewed_counts::approved_patch_operation_count",
        "PASS" if len(approved_df) >= 0 else "FAIL",
        f"actual={len(approved_df)}",
    )
    add_qa(
        "reviewed_counts::rejected_count",
        "PASS" if len(rejected_df) >= 0 else "FAIL",
        f"actual={len(rejected_df)}",
    )
    add_qa(
        "reviewed_counts::needs_more_info_count",
        "PASS" if len(needs_more_info_df) >= 0 else "FAIL",
        f"actual={len(needs_more_info_df)}",
    )
    add_qa(
        "safety::no_official_file_modification",
        "PASS",
        "325M reviewed validation only checks the workbook and does not modify official assets.",
    )
    add_qa(
        "safety::no_llm_or_api_call_executed",
        "PASS",
        "325M reviewed validation uses the 325M package and reviewed workbook only.",
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
        normalized_df.drop(columns=["human_approval_decision_normalized"], errors="ignore").to_dict(
            orient="records"
        )
        if not normalized_df.empty
        else [],
        key="human_approval_decision",
    )
    summary = {
        "stage": "325M-R",
        "mode": "validate-reviewed",
        "output_dir": "",
        "reviewed_workbook_path": str(reviewed_workbook),
        "source_approval_package_decision": _norm(approval_summary.get("decision")),
        "source_approval_package_qa_fail_count": _safe_int(approval_summary.get("qa_fail_count")),
        "approval_record_count": len(normalized_df),
        "approved_patch_operation_count": len(approved_df),
        "alias_approved_patch_operation_count": len(approved_df),
        "scope_approved_patch_operation_count": 0,
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
        "decision": final_decision if qa_fail_count == 0 else REVIEWED_NOT_READY_DECISION,
    }

    final_review_result_json = {
        "stage": "325M-R",
        "mode": "validate-reviewed",
        "decision": summary["decision"],
        "reviewed_workbook_path": str(reviewed_workbook),
        "approved_records": approved_df.drop(
            columns=["human_approval_decision_normalized"], errors="ignore"
        ).to_dict(orient="records"),
        "rejected_records": rejected_df.drop(
            columns=["human_approval_decision_normalized"], errors="ignore"
        ).to_dict(orient="records"),
        "needs_more_info_records": needs_more_info_df.drop(
            columns=["human_approval_decision_normalized"], errors="ignore"
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
            "# Controlled Alias Proposal Human Approval 325M Reviewed",
            "",
            "## Decision",
            f"- {summary.get('decision', '')}",
            "",
            "## Reviewed Counts",
            f"- approval_record_count: {summary.get('approval_record_count', 0)}",
            f"- approved_patch_operation_count: {summary.get('approved_patch_operation_count', 0)}",
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
            columns=["human_approval_decision_normalized"], errors="ignore"
        ),
        "rejected_df": rejected_df.drop(
            columns=["human_approval_decision_normalized"], errors="ignore"
        ),
        "needs_more_info_df": needs_more_info_df.drop(
            columns=["human_approval_decision_normalized"], errors="ignore"
        ),
        "all_reviewed_df": normalized_df.drop(
            columns=["human_approval_decision_normalized"], errors="ignore"
        ),
        "qa_summary_df": qa_summary_df,
        "qa_checks_df": qa_checks_df,
        "qa_json": qa_json,
        "final_review_result_json": final_review_result_json,
        "notes_markdown": notes_markdown,
    }
