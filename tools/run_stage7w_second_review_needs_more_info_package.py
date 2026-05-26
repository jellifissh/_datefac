import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

BASE_DIR = Path(r"D:\_datefac")

IN_V_DIR = BASE_DIR / "output" / "stage7v_sandbox_preview_from_validated_real_human_approval"
IN_V_SUMMARY = IN_V_DIR / "209_stage7v_sandbox_preview_from_validated_approval_summary.json"
IN_V_AUDIT = IN_V_DIR / "209_stage7v_candidate_filter_audit.xlsx"
IN_V_NOOP = IN_V_DIR / "209_stage7v_noop_safety_proof.json"
IN_V_GUARD = IN_V_DIR / "209_stage7v_blocked_value_mismatch_guard.json"

IN_U_DIR = BASE_DIR / "output" / "stage7u_real_human_approval_validation"
IN_U_SUMMARY = IN_U_DIR / "208_stage7u_real_human_approval_validation_summary.json"
IN_U_VALID = IN_U_DIR / "208_stage7u_validated_approval_results.xlsx"
IN_U_INVALID = IN_U_DIR / "208_stage7u_invalid_approval_results.xlsx"
IN_U_AUDIT = IN_U_DIR / "208_stage7u_validation_audit.xlsx"
IN_U_PROJECTION = IN_U_DIR / "208_stage7u_sandbox_preview_candidate_projection.xlsx"

OUT_DIR = BASE_DIR / "output" / "stage7w_second_review_needs_more_info_package"
OUT_SUMMARY = OUT_DIR / "210_stage7w_second_review_summary.json"
OUT_REPORT = OUT_DIR / "210_stage7w_second_review_report.md"
OUT_NEEDS_MORE_INFO = OUT_DIR / "210_stage7w_needs_more_info_questions.xlsx"
OUT_SECOND_REVIEW_QUEUE = OUT_DIR / "210_stage7w_second_review_queue.xlsx"
OUT_SECOND_REVIEW_TEMPLATE = OUT_DIR / "210_stage7w_second_review_input_template.xlsx"
OUT_POLICY = OUT_DIR / "210_stage7w_second_review_validation_policy.json"
OUT_NEXT_ACTION_AUDIT = OUT_DIR / "210_stage7w_next_action_audit.xlsx"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

SECOND_REVIEW_SCHEMA_VERSION = "stage7w_second_review_input_v1"


def _norm(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    if isinstance(v, str) and v.strip().lower() == "nan":
        return ""
    return str(v).strip()


def _as_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    return _norm(v).lower() in {"1", "true", "yes", "y"}


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _sha256(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _snapshot_hashes() -> Dict[str, str]:
    snap = s5k._snapshot_hashes()
    snap["official_02b"] = _sha256(OFFICIAL_02B)
    snap["formal_rules"] = _sha256(FORMAL_SCOPE_RULES)
    snap["standardizer"] = _sha256(STANDARDIZER_FILE)
    snap["release_zip"] = _sha256(RELEASE_ZIP)
    return snap


def _run_delivery_check() -> Dict[str, Any]:
    import subprocess

    p = subprocess.run(
        [sys.executable, str(BASE_DIR / "tools" / "check_delivery_state.py"), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    txt = (p.stdout or "").strip()
    return json.loads(txt) if txt else {"overall_status": "UNKNOWN"}


def _recommend_evidence(row: Dict[str, Any]) -> str:
    items: List[str] = []
    if _as_bool(row.get("value_mismatch")):
        items.append("Compare original PDF numeric cell against existing preview value")
    if "true_value_conflict" in _norm(row.get("conflict_type")).lower():
        items.append("Capture screenshot of source row and adjacent context")
    if "blocked_apply" in _norm(row.get("prior_stage_status")).lower():
        items.append("Review blocked_apply audit and confirm conflict key mapping")
    if not items:
        items.append("Recheck source evidence and reviewer rationale")
    return " | ".join(items)


def _next_required_action_for_needs_more_info(row: Dict[str, Any]) -> str:
    if _as_bool(row.get("value_mismatch")) or "true_value_conflict" in _norm(row.get("conflict_type")).lower():
        return "collect_source_evidence_and_trigger_second_review"
    return "collect_missing_information_then_revalidate"


def _next_required_action_for_second_review(row: Dict[str, Any]) -> str:
    if _as_bool(row.get("value_mismatch")):
        return "second_reviewer_must_confirm_corrected_value_or_escalate"
    if "true_value_conflict" in _norm(row.get("conflict_type")).lower():
        return "second_reviewer_must_reconcile_conflict_with_pdf_evidence"
    return "second_reviewer_confirmation_required"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    required = [
        IN_V_SUMMARY,
        IN_V_AUDIT,
        IN_V_NOOP,
        IN_V_GUARD,
        IN_U_SUMMARY,
        IN_U_VALID,
        IN_U_INVALID,
        IN_U_AUDIT,
        IN_U_PROJECTION,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "7W",
                "external_api_called": False,
                "real_apply_executed": False,
                "stage7v_summary_loaded": False,
                "blocked": True,
                "blocked_reason": f"missing_input:{'|'.join(missing)}",
            },
        )
        print("stage7w_status=blocked_missing_input")
        return 0

    before = _snapshot_hashes()

    stage7v_summary = _load_json(IN_V_SUMMARY)
    _ = pd.read_excel(IN_V_AUDIT)
    noop_proof = _load_json(IN_V_NOOP)
    guard = _load_json(IN_V_GUARD)

    stage7u_summary = _load_json(IN_U_SUMMARY)
    valid_df = pd.read_excel(IN_U_VALID)
    invalid_df = pd.read_excel(IN_U_INVALID)
    _ = pd.read_excel(IN_U_AUDIT)
    projection_df = pd.read_excel(IN_U_PROJECTION)

    stage7v_summary_loaded = True
    stage7u_validated_results_loaded = True

    stage7v_safety_ok = bool(
        stage7v_summary.get("stage7u_summary_loaded") is True
        and stage7v_summary.get("validated_approval_results_loaded") is True
        and stage7v_summary.get("candidate_projection_loaded") is True
        and int(stage7v_summary.get("sandbox_preview_candidate_count", -1)) == 0
        and int(stage7v_summary.get("sandbox_apply_attempt_count", -1)) == 0
        and int(stage7v_summary.get("sandbox_apply_success_count", -1)) == 0
        and stage7v_summary.get("no_op_due_to_zero_candidates") is True
        and int(stage7v_summary.get("fabricated_candidate_count", -1)) == 0
        and int(stage7v_summary.get("blocked_value_mismatch_auto_apply_count", -1)) == 0
        and _norm(stage7v_summary.get("check_delivery_state_overall_status")) == "PASS"
        and stage7v_summary.get("ready_for_stage7w_real_human_candidate_collection_or_second_review") is True
        and noop_proof.get("no_op_due_to_zero_candidates") is True
        and int(guard.get("blocked_value_mismatch_auto_apply_count", -1)) == 0
    )

    projection_map: Dict[str, Dict[str, Any]] = {}
    for _, prow in projection_df.iterrows():
        key = f"{_norm(prow.get('queue_item_id'))}::{_norm(prow.get('suggestion_id'))}"
        projection_map[key] = prow.to_dict()

    rows: List[Dict[str, Any]] = []
    for _, r in valid_df.iterrows():
        row = r.to_dict()
        key = f"{_norm(row.get('queue_item_id'))}::{_norm(row.get('suggestion_id'))}"
        p = projection_map.get(key, {})
        row["projection_row_valid"] = _as_bool(p.get("row_valid"))
        row["projection_candidate"] = _as_bool(p.get("sandbox_preview_candidate"))
        rows.append(row)

    needs_more_info_rows: List[Dict[str, Any]] = []
    second_review_rows: List[Dict[str, Any]] = []
    rejected_rows: List[Dict[str, Any]] = []
    not_candidate_other_rows: List[Dict[str, Any]] = []
    approve_rows: List[Dict[str, Any]] = []
    approve_rechecked_rows: List[Dict[str, Any]] = []
    next_action_rows: List[Dict[str, Any]] = []

    value_mismatch_forced_second_review_count = 0

    for row in rows:
        decision = _norm(row.get("human_decision"))
        value_mismatch = _as_bool(row.get("value_mismatch"))
        conflict_type = _norm(row.get("conflict_type")).lower()
        prior_stage_status = _norm(row.get("prior_stage_status")).lower()
        corrected_fields_present = any(
            _norm(row.get(x))
            for x in ["corrected_metric_name", "corrected_value", "corrected_unit", "corrected_fiscal_year"]
        )
        forced_second_review = bool(
            value_mismatch
            or "true_value_conflict" in conflict_type
            or "blocked_apply" in prior_stage_status
            or "unresolved_conflict" in prior_stage_status
        )

        if decision == "NEEDS_MORE_INFO":
            needs_more_info_rows.append(row)
        elif decision == "REQUIRE_SECOND_REVIEW":
            second_review_rows.append(row)
        elif decision == "REJECT":
            rejected_rows.append(row)
        elif decision == "APPROVE_FOR_SANDBOX_PREVIEW":
            approve_rows.append(row)
        else:
            not_candidate_other_rows.append(row)

        if forced_second_review and decision != "REQUIRE_SECOND_REVIEW":
            second_review_rows.append(row)
        if forced_second_review and value_mismatch:
            value_mismatch_forced_second_review_count += 1

        if decision == "APPROVE_FOR_SANDBOX_PREVIEW":
            recheck_fail_reasons: List[str] = []
            if not _as_bool(row.get("row_valid")) and not _as_bool(row.get("projection_row_valid")):
                recheck_fail_reasons.append("row_not_valid")
            if not _as_bool(row.get("projection_candidate")):
                recheck_fail_reasons.append("projection_not_candidate")
            if value_mismatch:
                recheck_fail_reasons.append("value_mismatch_true")
            if "true_value_conflict" in conflict_type:
                recheck_fail_reasons.append("true_value_conflict")
            if "blocked_apply" in prior_stage_status or "unresolved_conflict" in prior_stage_status:
                recheck_fail_reasons.append("prior_stage_blocked_or_unresolved")
            if corrected_fields_present:
                recheck_fail_reasons.append("corrected_fields_present")
            approve_rechecked_rows.append(
                {
                    "queue_item_id": _norm(row.get("queue_item_id")),
                    "suggestion_id": _norm(row.get("suggestion_id")),
                    "approve_recheck_pass": len(recheck_fail_reasons) == 0,
                    "approve_recheck_fail_reasons": "|".join(recheck_fail_reasons),
                }
            )

    # Deduplicate second-review queue by queue_item_id + suggestion_id
    second_review_dedup: Dict[str, Dict[str, Any]] = {}
    for row in second_review_rows:
        key = f"{_norm(row.get('queue_item_id'))}::{_norm(row.get('suggestion_id'))}"
        second_review_dedup[key] = row
    second_review_rows = list(second_review_dedup.values())

    needs_more_info_columns = [
        "queue_item_id",
        "suggestion_id",
        "source_pdf",
        "source_page",
        "source_row_reference",
        "statement_type",
        "fiscal_year",
        "original_metric_name",
        "suggested_metric_name",
        "suggested_value",
        "suggested_unit",
        "existing_metric_name",
        "existing_value",
        "existing_unit",
        "conflict_type",
        "value_mismatch",
        "prior_stage_status",
        "reviewer_id",
        "reviewer_notes",
        "needs_more_info_question",
        "recommended_evidence_to_collect",
        "next_required_action",
    ]
    needs_more_info_payload: List[Dict[str, Any]] = []
    for row in needs_more_info_rows:
        out = {k: row.get(k, "") for k in needs_more_info_columns}
        out["recommended_evidence_to_collect"] = _recommend_evidence(row)
        out["next_required_action"] = _next_required_action_for_needs_more_info(row)
        needs_more_info_payload.append(out)
        next_action_rows.append(
            {
                "queue_item_id": _norm(row.get("queue_item_id")),
                "suggestion_id": _norm(row.get("suggestion_id")),
                "current_bucket": "NEEDS_MORE_INFO",
                "next_required_action": out["next_required_action"],
            }
        )
    needs_more_info_df = pd.DataFrame(needs_more_info_payload, columns=needs_more_info_columns)
    needs_more_info_df.to_excel(
        OUT_NEEDS_MORE_INFO,
        sheet_name="needs_more_info_questions",
        index=False,
        engine="openpyxl",
    )

    second_review_columns = [
        "queue_item_id",
        "suggestion_id",
        "source_pdf",
        "source_page",
        "source_row_reference",
        "statement_type",
        "fiscal_year",
        "original_metric_name",
        "suggested_metric_name",
        "suggested_value",
        "suggested_unit",
        "existing_metric_name",
        "existing_value",
        "existing_unit",
        "conflict_type",
        "value_mismatch",
        "prior_stage_status",
        "reviewer_id",
        "reviewer_notes",
        "second_review_required",
        "second_reviewer_id",
        "second_review_notes",
        "recommended_second_review_focus",
        "next_required_action",
    ]
    second_review_payload: List[Dict[str, Any]] = []
    for row in second_review_rows:
        out = {k: row.get(k, "") for k in second_review_columns}
        out["second_review_required"] = True
        out["recommended_second_review_focus"] = _recommend_evidence(row)
        out["next_required_action"] = _next_required_action_for_second_review(row)
        second_review_payload.append(out)
        next_action_rows.append(
            {
                "queue_item_id": _norm(row.get("queue_item_id")),
                "suggestion_id": _norm(row.get("suggestion_id")),
                "current_bucket": "REQUIRE_SECOND_REVIEW",
                "next_required_action": out["next_required_action"],
            }
        )
    second_review_df = pd.DataFrame(second_review_payload, columns=second_review_columns)
    second_review_df.to_excel(
        OUT_SECOND_REVIEW_QUEUE,
        sheet_name="second_review_queue",
        index=False,
        engine="openpyxl",
    )

    template_columns = [
        "schema_version",
        "queue_item_id",
        "suggestion_id",
        "source_pdf",
        "source_page",
        "source_row_reference",
        "statement_type",
        "fiscal_year",
        "original_metric_name",
        "suggested_metric_name",
        "suggested_value",
        "suggested_unit",
        "existing_metric_name",
        "existing_value",
        "existing_unit",
        "conflict_type",
        "value_mismatch",
        "prior_stage_status",
        "second_reviewer_id",
        "second_reviewer_role",
        "second_review_decision",
        "second_review_reason_code",
        "second_review_notes",
        "source_row_rechecked",
        "fiscal_year_rechecked",
        "unit_rechecked",
        "value_rechecked",
        "original_pdf_evidence_checked",
        "corrected_metric_name",
        "corrected_value",
        "corrected_unit",
        "corrected_fiscal_year",
        "remaining_question",
        "reviewed_at_utc",
    ]
    template_rows: List[Dict[str, Any]] = []
    for row in second_review_rows:
        template_rows.append(
            {
                "schema_version": SECOND_REVIEW_SCHEMA_VERSION,
                "queue_item_id": _norm(row.get("queue_item_id")),
                "suggestion_id": _norm(row.get("suggestion_id")),
                "source_pdf": _norm(row.get("source_pdf")),
                "source_page": _norm(row.get("source_page")),
                "source_row_reference": _norm(row.get("source_row_reference")),
                "statement_type": _norm(row.get("statement_type")),
                "fiscal_year": _norm(row.get("fiscal_year")),
                "original_metric_name": _norm(row.get("original_metric_name")),
                "suggested_metric_name": _norm(row.get("suggested_metric_name")),
                "suggested_value": _norm(row.get("suggested_value")),
                "suggested_unit": _norm(row.get("suggested_unit")),
                "existing_metric_name": _norm(row.get("existing_metric_name")),
                "existing_value": _norm(row.get("existing_value")),
                "existing_unit": _norm(row.get("existing_unit")),
                "conflict_type": _norm(row.get("conflict_type")),
                "value_mismatch": _as_bool(row.get("value_mismatch")),
                "prior_stage_status": _norm(row.get("prior_stage_status")),
                "second_reviewer_id": "",
                "second_reviewer_role": "",
                "second_review_decision": "",
                "second_review_reason_code": "",
                "second_review_notes": "",
                "source_row_rechecked": "",
                "fiscal_year_rechecked": "",
                "unit_rechecked": "",
                "value_rechecked": "",
                "original_pdf_evidence_checked": "",
                "corrected_metric_name": "",
                "corrected_value": "",
                "corrected_unit": "",
                "corrected_fiscal_year": "",
                "remaining_question": "",
                "reviewed_at_utc": "",
            }
        )
    template_df = pd.DataFrame(template_rows, columns=template_columns)
    template_df.to_excel(
        OUT_SECOND_REVIEW_TEMPLATE,
        sheet_name="second_review_input_template",
        index=False,
        engine="openpyxl",
    )

    policy = {
        "schema_version": SECOND_REVIEW_SCHEMA_VERSION,
        "second_review_decision_enum": [
            "CONFIRM_NEEDS_MORE_INFO",
            "CONFIRM_REJECT",
            "APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE",
            "ESCALATE_TO_MANUAL_ACCOUNTING_REVIEW",
        ],
        "forbidden_decisions": ["APPROVE_FOR_REAL_APPLY"],
        "forbidden_human_fields": ["safe_to_apply"],
        "validation_rules": [
            "second_reviewer_id required",
            "second_review_decision required",
            "second_review_decision must be in enum",
            "source_row_rechecked=true required for APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE",
            "fiscal_year_rechecked=true required for APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE",
            "unit_rechecked=true required for APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE",
            "value_rechecked=true required for APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE",
            "original_pdf_evidence_checked=true required for APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE",
            "value_mismatch=true cannot become candidate unless corrected_value is explicitly provided and reviewed",
            "true_value_conflict must be escalated or require explicit corrected evidence",
            "corrected fields only produce candidate for future sandbox preview validation, never safe_to_apply",
            "any APPROVE_FOR_REAL_APPLY is invalid",
            "any safe_to_apply field supplied by human input is invalid",
        ],
    }
    _write_json(OUT_POLICY, policy)

    next_action_df = pd.DataFrame(
        next_action_rows,
        columns=["queue_item_id", "suggestion_id", "current_bucket", "next_required_action"],
    ).drop_duplicates(subset=["queue_item_id", "suggestion_id", "current_bucket"])
    next_action_df.to_excel(OUT_NEXT_ACTION_AUDIT, sheet_name="next_action_audit", index=False, engine="openpyxl")

    after = _snapshot_hashes()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery_state = _run_delivery_check()

    sandbox_preview_candidate_count = int(stage7v_summary.get("sandbox_preview_candidate_count", 0))
    sandbox_apply_attempt_count = int(stage7v_summary.get("sandbox_apply_attempt_count", 0))
    sandbox_apply_success_count = int(stage7v_summary.get("sandbox_apply_success_count", 0))
    no_op_due_to_zero_candidates = bool(stage7v_summary.get("no_op_due_to_zero_candidates") is True)
    fabricated_candidate_count = int(stage7v_summary.get("fabricated_candidate_count", 0))
    blocked_value_mismatch_auto_apply_count = int(stage7v_summary.get("blocked_value_mismatch_auto_apply_count", 0))
    approve_for_real_apply_detected_count = int(stage7v_summary.get("approve_for_real_apply_detected_count", 0))

    summary = {
        "stage": "7W",
        "external_api_called": False,
        "real_apply_executed": False,
        "stage7v_summary_loaded": stage7v_summary_loaded,
        "stage7u_validated_results_loaded": stage7u_validated_results_loaded,
        "sandbox_preview_candidate_count": sandbox_preview_candidate_count,
        "sandbox_apply_attempt_count": sandbox_apply_attempt_count,
        "sandbox_apply_success_count": sandbox_apply_success_count,
        "no_op_due_to_zero_candidates": no_op_due_to_zero_candidates,
        "needs_more_info_count": len(needs_more_info_rows),
        "require_second_review_count": len(second_review_rows),
        "second_review_queue_generated": True,
        "needs_more_info_package_generated": True,
        "second_review_input_template_generated": True,
        "second_review_validation_policy_generated": True,
        "approve_for_sandbox_preview_generated_count": len(approve_rows),
        "approve_for_real_apply_detected_count": approve_for_real_apply_detected_count,
        "fabricated_candidate_count": fabricated_candidate_count,
        "blocked_value_mismatch_auto_apply_count": blocked_value_mismatch_auto_apply_count,
        "value_mismatch_forced_second_review_count": value_mismatch_forced_second_review_count,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": _norm(delivery_state.get("overall_status")),
        "stage7v_safety_state_verified": stage7v_safety_ok,
        "validated_approval_count": len(valid_df),
        "invalid_approval_count": len(invalid_df),
        "rejected_by_human_count": len(rejected_rows),
        "not_candidate_other_count": len(not_candidate_other_rows),
        "approve_recheck_row_count": len(approve_rechecked_rows),
        "ready_for_stage7x_second_review_input_validation": True,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# Stage 7W Second Review / Needs More Info Package",
        "",
        "Mode: no API call, no real apply, no production write.",
        "",
        "## Inputs",
        f"- Stage7V summary loaded: {stage7v_summary_loaded}",
        f"- Stage7U validated results loaded: {stage7u_validated_results_loaded}",
        f"- Stage7V safety state verified: {stage7v_safety_ok}",
        "",
        "## Classification",
        f"- NEEDS_MORE_INFO: {len(needs_more_info_rows)}",
        f"- REQUIRE_SECOND_REVIEW queue: {len(second_review_rows)}",
        f"- REJECTED_BY_HUMAN: {len(rejected_rows)}",
        f"- APPROVE_FOR_SANDBOX_PREVIEW (reported only): {len(approve_rows)}",
        "",
        "## Safety Guard",
        f"- sandbox_preview_candidate_count: {sandbox_preview_candidate_count}",
        f"- sandbox_apply_attempt_count: {sandbox_apply_attempt_count}",
        f"- sandbox_apply_success_count: {sandbox_apply_success_count}",
        f"- no_op_due_to_zero_candidates: {no_op_due_to_zero_candidates}",
        f"- fabricated_candidate_count: {fabricated_candidate_count}",
        f"- blocked_value_mismatch_auto_apply_count: {blocked_value_mismatch_auto_apply_count}",
        "",
        "## Note",
        "- Stage7W only generates second-review / needs-more-info tasks.",
        "- It does not apply to sandbox preview and does not write production.",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print("stage7w_status=ok")
    print(f"stage7w_summary={OUT_SUMMARY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
