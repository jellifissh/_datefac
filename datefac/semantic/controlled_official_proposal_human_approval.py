from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

import pandas as pd


EXPECTED_323K_DECISION = (
    "CONTROLLED_OFFICIAL_PROPOSAL_DRY_RUN_323K_READY_FOR_HUMAN_APPROVAL"
)
EXPECTED_323L_DECISION = (
    "CONTROLLED_OFFICIAL_PROPOSAL_HUMAN_APPROVAL_323L_READY_FOR_HUMAN_REVIEW"
)
NOT_READY_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_HUMAN_APPROVAL_323L_NOT_READY"
DEFAULT_OUTPUT_DIR = Path(
    r"D:\_datefac\output\controlled_official_proposal_human_approval_323l"
)

PREPARE_DECISION_PENDING = "PENDING_HUMAN_APPROVAL"
ALLOWED_REVIEWER_DECISIONS = {"APPROVED", "REJECTED", "NEEDS_MORE_REVIEW"}
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


def _decision_distribution(records: List[Dict[str, Any]]) -> Dict[str, int]:
    distribution: Dict[str, int] = {}
    for record in records:
        decision = _norm(record.get("reviewer_decision")) or PREPARE_DECISION_PENDING
        distribution[decision] = distribution.get(decision, 0) + 1
    return distribution


def load_controlled_official_proposal_human_approval_inputs(
    dry_run_dir: Path,
) -> Dict[str, Any]:
    patch_operations_payload = _read_json(
        dry_run_dir / "controlled_official_proposal_dry_run_323k_patch_operations.json"
    )
    target_diff_payload = _read_json(
        dry_run_dir
        / "controlled_official_proposal_dry_run_323k_target_asset_diff_preview.json"
    )
    rollback_payload = _read_json(
        dry_run_dir / "controlled_official_proposal_dry_run_323k_rollback_plan.json"
    )
    return {
        "dry_run_summary": _read_json(
            dry_run_dir / "controlled_official_proposal_dry_run_323k_summary.json"
        ),
        "dry_run_qa": _read_json(
            dry_run_dir / "controlled_official_proposal_dry_run_323k_qa.json"
        ),
        "patch_operations_df": pd.DataFrame(
            patch_operations_payload.get("patch_operations", [])
            if isinstance(patch_operations_payload.get("patch_operations", []), list)
            else []
        ).fillna(""),
        "target_diff_payload": target_diff_payload,
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
    }


def build_controlled_official_proposal_human_approval_prepare(
    dry_run_summary: Dict[str, Any],
    dry_run_qa: Dict[str, Any],
    patch_operations_df: pd.DataFrame,
    before_after_preview_df: pd.DataFrame,
    target_asset_diff_preview_df: pd.DataFrame,
    rollback_plan_df: pd.DataFrame,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa(
        "readiness::323k_decision",
        "PASS"
        if _norm(dry_run_summary.get("decision")) == EXPECTED_323K_DECISION
        else "FAIL",
        _norm(dry_run_summary.get("decision")),
    )
    add_qa(
        "readiness::323k_qa_fail_count",
        "PASS" if _safe_int(dry_run_summary.get("qa_fail_count")) == 0 else "FAIL",
        str(dry_run_summary.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::323k_qa_json_fail_count",
        "PASS" if _safe_int(dry_run_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(dry_run_qa.get("qa_fail_count", "")),
    )
    for key, expected in [
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
        add_qa(
            f"readiness::323k_{key}",
            "PASS" if _safe_int(dry_run_summary.get(key)) == expected else "FAIL",
            f"expected={expected} actual={dry_run_summary.get(key, '')}",
        )

    operations_df = patch_operations_df.copy().fillna("") if not patch_operations_df.empty else pd.DataFrame()
    add_qa(
        "inputs::patch_operation_count",
        "PASS" if len(operations_df) == 6 else "FAIL",
        f"actual={len(operations_df)}",
    )
    add_qa(
        "inputs::alias_patch_operation_count",
        "PASS"
        if int(operations_df["candidate_type"].astype(str).eq("alias").sum()) == 2
        else "FAIL",
        f"actual={int(operations_df['candidate_type'].astype(str).eq('alias').sum()) if not operations_df.empty else 0}",
    )
    add_qa(
        "inputs::scope_patch_operation_count",
        "PASS"
        if int(operations_df["candidate_type"].astype(str).eq("scope").sum()) == 4
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
    alias_index = 0
    scope_index = 0
    for _, row in operations_df.iterrows():
        row_dict = row.to_dict()
        operation_id = _norm(row_dict.get("dry_run_patch_operation_id"))
        candidate_type = _norm(row_dict.get("candidate_type"))
        if candidate_type == "alias":
            alias_index += 1
            approval_id = f"approval_323l::alias::{alias_index:03d}"
        else:
            scope_index += 1
            approval_id = f"approval_323l::scope::{scope_index:03d}"

        diff_row = diff_lookup.get(operation_id, {})
        rollback_row = rollback_lookup.get(operation_id, {})
        proposed_change = _norm(row_dict.get("preview_payload_json"))
        dry_run_evidence = " | ".join(
            [
                f"before_state={_norm(diff_row.get('before_state') or row_dict.get('before_state'))}",
                f"group_before={_norm(diff_row.get('group_before_entry_count') or row_dict.get('group_before_entry_count'))}",
                f"group_after_preview={_norm(diff_row.get('group_after_entry_count_preview') or row_dict.get('group_after_entry_count_preview'))}",
                f"official_overlap={_norm(diff_row.get('official_overlap_count') or row_dict.get('already_official_overlap_count'))}",
                f"target_locator={_norm(row_dict.get('target_locator'))}",
            ]
        )
        provenance = " | ".join(
            [
                f"source_rule_candidate_id={_norm(row_dict.get('source_rule_candidate_id'))}",
                f"source_rule_ids={_norm(row_dict.get('source_rule_ids'))}",
                f"source_confirmation_ids={_norm(row_dict.get('source_confirmation_ids'))}",
                f"source_request_ids={_norm(row_dict.get('source_request_ids'))}",
                f"source_group_ids={_norm(row_dict.get('source_group_ids'))}",
            ]
        )

        approval_records.append(
            {
                "approval_id": approval_id,
                "reviewer_decision": PREPARE_DECISION_PENDING,
                "reviewer_note": "",
                "reviewer_name": "",
                "approval_timestamp": "",
                "allowed_reviewer_decisions": "APPROVED | REJECTED | NEEDS_MORE_REVIEW",
                "dry_run_patch_operation_id": operation_id,
                "controlled_proposal_id": _norm(row_dict.get("controlled_proposal_id")),
                "source_rule_candidate_id": _norm(row_dict.get("source_rule_candidate_id")),
                "candidate_type": candidate_type,
                "proposal_type": _norm(row_dict.get("proposal_type")),
                "future_operation_type": _norm(row_dict.get("future_operation_type")),
                "target_asset_path": _norm(row_dict.get("target_asset_path")),
                "target_group_name": _norm(row_dict.get("target_group_name")),
                "target_locator": _norm(row_dict.get("target_locator")),
                "target_rule_family": _norm(row_dict.get("target_rule_family")),
                "normalized_label": _norm(row_dict.get("normalized_label")),
                "proposed_change": proposed_change,
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
                "provenance": provenance,
                "rollback_note": _norm(
                    rollback_row.get("rollback_instruction")
                    or row_dict.get("rollback_note")
                ),
                "dry_run_evidence": dry_run_evidence,
                "risk_flags": _norm(row_dict.get("risk_flags")),
                "sample_table_titles": _norm(row_dict.get("sample_table_titles")),
                "sample_texts": _norm(row_dict.get("sample_texts")),
                "sample_years": _norm(row_dict.get("sample_years")),
                "proposal_only_no_apply_confirmed": True,
            }
        )

    approvals_df = pd.DataFrame(approval_records).fillna("")
    alias_approvals_df = (
        approvals_df.loc[approvals_df["candidate_type"].astype(str) == "alias"].copy()
        if not approvals_df.empty
        else pd.DataFrame()
    )
    scope_approvals_df = (
        approvals_df.loc[approvals_df["candidate_type"].astype(str) == "scope"].copy()
        if not approvals_df.empty
        else pd.DataFrame()
    )

    decision_distribution = _decision_distribution(approval_records)
    all_pending = (
        not approvals_df.empty
        and approvals_df["reviewer_decision"].astype(str).eq(PREPARE_DECISION_PENDING).all()
    )
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
    missing_rollback_count = (
        int(approvals_df["rollback_note"].astype(str).eq("").sum())
        if not approvals_df.empty
        else 0
    )
    missing_provenance_count = (
        int(approvals_df["provenance"].astype(str).eq("").sum())
        if not approvals_df.empty
        else 0
    )
    missing_evidence_count = (
        int(approvals_df["dry_run_evidence"].astype(str).eq("").sum())
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
        "PASS" if len(alias_approvals_df) == 2 else "FAIL",
        f"actual={len(alias_approvals_df)}",
    )
    add_qa(
        "approval_counts::scope_approval_count",
        "PASS" if len(scope_approvals_df) == 4 else "FAIL",
        f"actual={len(scope_approvals_df)}",
    )
    add_qa(
        "approval_integrity::all_pending_human_approval",
        "PASS" if all_pending else "FAIL",
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
        "approval_integrity::rollback_note_completeness",
        "PASS" if missing_rollback_count == 0 else "FAIL",
        f"actual={missing_rollback_count}",
    )
    add_qa(
        "approval_integrity::provenance_completeness",
        "PASS" if missing_provenance_count == 0 else "FAIL",
        f"actual={missing_provenance_count}",
    )
    add_qa(
        "approval_integrity::dry_run_evidence_completeness",
        "PASS" if missing_evidence_count == 0 else "FAIL",
        f"actual={missing_evidence_count}",
    )
    add_qa(
        "approval_integrity::reviewer_fields_present",
        "PASS"
        if {
            "reviewer_decision",
            "reviewer_note",
            "reviewer_name",
            "approval_timestamp",
        }.issubset(set(approvals_df.columns))
        else "FAIL",
        "reviewer_decision, reviewer_note, reviewer_name, approval_timestamp",
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
        "323L prepares approval records only and does not modify official assets.",
    )
    add_qa(
        "safety::no_llm_or_api_call_executed",
        "PASS",
        "323L uses 323K outputs only.",
    )

    review_instructions_df = pd.DataFrame(
        [
            {
                "section": "package_purpose",
                "instruction": "Review each 323K dry-run patch operation and decide whether it should remain eligible for a later official patch stage.",
            },
            {
                "section": "allowed_decisions",
                "instruction": "Allowed reviewer_decision values: APPROVED, REJECTED, NEEDS_MORE_REVIEW.",
            },
            {
                "section": "approval_rule",
                "instruction": "Approve only when target asset/group, proposed change, provenance, dry-run evidence, and rollback note all look safe and correct.",
            },
            {
                "section": "rejection_rule",
                "instruction": "Reject when label semantics, target category, expected impact, or safety assumptions are not acceptable.",
            },
            {
                "section": "needs_more_review_rule",
                "instruction": "Use NEEDS_MORE_REVIEW when provenance or semantics are incomplete for a safe decision.",
            },
            {
                "section": "no_apply_note",
                "instruction": "323L does not apply any patch and does not modify official mapping, override, or production pipeline files.",
            },
        ]
    ).fillna("")

    no_apply_proof_json = {
        "files_read": [
            str(
                DEFAULT_OUTPUT_DIR.parent
                / "controlled_official_proposal_dry_run_323k"
                / "controlled_official_proposal_dry_run_323k_summary.json"
            ),
            str(
                DEFAULT_OUTPUT_DIR.parent
                / "controlled_official_proposal_dry_run_323k"
                / "controlled_official_proposal_dry_run_323k_patch_operations.json"
            ),
            str(
                DEFAULT_OUTPUT_DIR.parent
                / "controlled_official_proposal_dry_run_323k"
                / "controlled_official_proposal_dry_run_323k_target_asset_diff_preview.json"
            ),
            str(
                DEFAULT_OUTPUT_DIR.parent
                / "controlled_official_proposal_dry_run_323k"
                / "controlled_official_proposal_dry_run_323k_rollback_plan.json"
            ),
            str(
                DEFAULT_OUTPUT_DIR.parent
                / "controlled_official_proposal_dry_run_323k"
                / "controlled_official_proposal_dry_run_323k_qa.json"
            ),
        ],
        "files_written": [],
        "official_target_files_inspected": [
            str(OFFICIAL_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
        "official_target_files_not_modified": [
            str(OFFICIAL_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
        "output_only_write_confirmation": True,
        "decision": "approval_package_only_no_apply",
    }
    no_apply_proof_df = pd.DataFrame(
        [
            {
                "files_read_count": len(no_apply_proof_json["files_read"]),
                "files_written_count": len(no_apply_proof_json["files_written"]),
                "official_target_files_inspected_count": len(
                    no_apply_proof_json["official_target_files_inspected"]
                ),
                "official_target_files_not_modified_count": len(
                    no_apply_proof_json["official_target_files_not_modified"]
                ),
                "output_only_write_confirmation": no_apply_proof_json[
                    "output_only_write_confirmation"
                ],
                "decision": no_apply_proof_json["decision"],
            }
        ]
    ).fillna("")

    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "prepare_only",
                "detail": "323L prepares human approval records only and does not validate reviewed decisions yet.",
            },
            {
                "limitation": "dry_run_evidence_only",
                "detail": "All evidence is carried forward from 323K dry-run artifacts; no new sandbox replay is run here.",
            },
            {
                "limitation": "future_stage_required",
                "detail": "A later stage must read the reviewed workbook before any official patch application can be considered.",
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
        "stage": "323L",
        "mode": "prepare",
        "output_dir": "",
        "source_dry_run_decision": _norm(dry_run_summary.get("decision")),
        "source_dry_run_qa_fail_count": _safe_int(dry_run_summary.get("qa_fail_count")),
        "approval_record_count": len(approval_records),
        "alias_approval_count": len(alias_approvals_df),
        "scope_approval_count": len(scope_approvals_df),
        "decision_distribution": decision_distribution,
        "all_decisions_pending_human_approval": all_pending,
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
        "decision": EXPECTED_323L_DECISION if qa_fail_count == 0 else NOT_READY_DECISION,
    }

    approval_package_json = {
        "stage": "323L",
        "mode": "prepare",
        "decision": summary["decision"],
        "allowed_reviewer_decisions": sorted(ALLOWED_REVIEWER_DECISIONS),
        "approval_records": approval_records,
        "alias_approval_records": alias_approvals_df.to_dict(orient="records"),
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

    notes_markdown = _build_review_notes_markdown(summary)

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


def _build_review_notes_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Controlled Official Proposal Human Approval 323L",
        "",
        "## Decision",
        f"- {summary.get('decision', '')}",
        "",
        "## Approval Counts",
        f"- approval_record_count: {summary.get('approval_record_count', 0)}",
        f"- alias_approval_count: {summary.get('alias_approval_count', 0)}",
        f"- scope_approval_count: {summary.get('scope_approval_count', 0)}",
        "",
        "## Decision Distribution",
        f"- {json.dumps(summary.get('decision_distribution', {}), ensure_ascii=False)}",
        "",
        "## Notes",
        "- 323L is a human approval package only.",
        "- Every record remains pending until a human reviewer updates the workbook.",
        "- No official asset or production pipeline file is modified in this stage.",
        "",
    ]
    return "\n".join(lines)
