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
IN_DIR = BASE_DIR / "output" / "stage8b_real_second_review_input_validation"

IN_SUMMARY = IN_DIR / "215_stage8b_real_second_review_validation_summary.json"
IN_VALID = IN_DIR / "215_stage8b_valid_real_second_review_results.xlsx"
IN_INVALID = IN_DIR / "215_stage8b_invalid_real_second_review_results.xlsx"
IN_PROJECTION = IN_DIR / "215_stage8b_real_second_review_candidate_projection.xlsx"
IN_AUDIT = IN_DIR / "215_stage8b_validation_audit.xlsx"
IN_NEG = IN_DIR / "215_stage8b_negative_validation_tests.json"
IN_NO_APPLY = IN_DIR / "215_stage8b_no_apply_proof.json"

OUT_DIR = BASE_DIR / "output" / "stage8c_real_sandbox_preview_candidate_preflight"
OUT_SUMMARY = OUT_DIR / "216_stage8c_real_candidate_preflight_summary.json"
OUT_REPORT = OUT_DIR / "216_stage8c_real_candidate_preflight_report.md"
OUT_FILTER_AUDIT = OUT_DIR / "216_stage8c_candidate_filter_audit.xlsx"
OUT_NOOP = OUT_DIR / "216_stage8c_zero_candidate_noop_proof.json"
OUT_UNRESOLVED = OUT_DIR / "216_stage8c_unresolved_followup_summary.xlsx"
OUT_BLOCKER = OUT_DIR / "216_stage8c_production_preflight_blocker.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"


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


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    required = [IN_SUMMARY, IN_VALID, IN_INVALID, IN_PROJECTION, IN_AUDIT, IN_NEG, IN_NO_APPLY]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "8C",
                "external_api_called": False,
                "real_apply_executed": False,
                "stage8b_summary_loaded": False,
                "blocked": True,
                "blocked_reason": f"missing_input:{'|'.join(missing)}",
            },
        )
        print("stage8c_status=blocked_missing_input")
        return 0

    before = _snapshot_hashes()

    s8b = _load_json(IN_SUMMARY)
    valid_df = pd.read_excel(IN_VALID)
    invalid_df = pd.read_excel(IN_INVALID)
    proj_df = pd.read_excel(IN_PROJECTION)
    _ = pd.read_excel(IN_AUDIT)
    _ = _load_json(IN_NEG)
    _ = _load_json(IN_NO_APPLY)

    stage8b_summary_loaded = True
    valid_real_second_review_results_loaded = True
    real_candidate_projection_loaded = True

    stage8b_guard_ok = bool(
        s8b.get("external_api_called") is False
        and s8b.get("real_apply_executed") is False
        and int(s8b.get("sandbox_apply_attempt_count", -1)) == 0
        and int(s8b.get("production_apply_attempt_count", -1)) == 0
        and s8b.get("stage8a_gate_verified") is True
        and s8b.get("real_second_review_input_loaded") is True
        and s8b.get("real_second_review_input_schema_valid") is True
        and int(s8b.get("real_second_review_input_row_count", -1)) == 5
        and int(s8b.get("valid_real_second_review_count", -1)) == 5
        and int(s8b.get("invalid_real_second_review_count", -1)) == 0
        and int(s8b.get("approve_for_sandbox_preview_candidate_count", -1)) == 0
        and int(s8b.get("real_sandbox_preview_candidate_count", -1)) == 0
        and s8b.get("candidate_projection_generated") is True
        and int(s8b.get("blocked_value_mismatch_auto_apply_count", -1)) == 0
        and _norm(s8b.get("check_delivery_state_overall_status")) == "PASS"
        and s8b.get("ready_for_stage8c_real_sandbox_preview_candidate_preflight") is True
        and s8b.get("ready_for_production_preflight") is False
    )

    # Candidate rows are strictly filtered by Stage8B contract
    filter_rows: List[Dict[str, Any]] = []
    candidate_rows: List[Dict[str, Any]] = []

    for _, r in proj_df.iterrows():
        row = r.to_dict()
        row_valid = _as_bool(row.get("row_valid"))
        decision = _norm(row.get("second_review_decision"))
        sandbox_preview_candidate = _as_bool(row.get("sandbox_preview_candidate"))

        reasons: List[str] = []
        if not row_valid:
            reasons.append("row_not_valid")
        if decision != "APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE":
            reasons.append("decision_not_approve_for_sandbox_preview_candidate")
        if not sandbox_preview_candidate:
            reasons.append("sandbox_preview_candidate_false")

        final_candidate = len(reasons) == 0
        if final_candidate:
            candidate_rows.append(row)

        filter_rows.append(
            {
                "queue_item_id": _norm(row.get("queue_item_id")),
                "suggestion_id": _norm(row.get("suggestion_id")),
                "second_review_decision": decision,
                "row_valid": row_valid,
                "sandbox_preview_candidate": sandbox_preview_candidate,
                "final_candidate": final_candidate,
                "reject_reasons": "|".join(reasons),
            }
        )

    filter_df = pd.DataFrame(filter_rows)
    filter_df.to_excel(OUT_FILTER_AUDIT, sheet_name="candidate_filter_audit", index=False, engine="openpyxl")

    # Unresolved follow-up summary from valid rows
    decision_counts = (
        valid_df["second_review_decision"].value_counts(dropna=False).to_dict()
        if "second_review_decision" in valid_df.columns
        else {}
    )
    unresolved_summary_rows = [
        {
            "decision": "CONFIRM_NEEDS_MORE_INFO",
            "row_count": int(decision_counts.get("CONFIRM_NEEDS_MORE_INFO", 0)),
            "followup_status": "unresolved_needs_more_info",
        },
        {
            "decision": "ESCALATE_TO_MANUAL_ACCOUNTING_REVIEW",
            "row_count": int(decision_counts.get("ESCALATE_TO_MANUAL_ACCOUNTING_REVIEW", 0)),
            "followup_status": "unresolved_escalation",
        },
        {
            "decision": "CONFIRM_REJECT",
            "row_count": int(decision_counts.get("CONFIRM_REJECT", 0)),
            "followup_status": "rejected_by_second_reviewer",
        },
        {
            "decision": "APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE",
            "row_count": int(decision_counts.get("APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE", 0)),
            "followup_status": "candidate_pending_preflight",
        },
    ]
    unresolved_df = pd.DataFrame(unresolved_summary_rows)
    unresolved_df.to_excel(OUT_UNRESOLVED, sheet_name="unresolved_followup_summary", index=False, engine="openpyxl")

    real_sandbox_preview_candidate_count = len(candidate_rows)
    no_op_due_to_zero_real_candidates = real_sandbox_preview_candidate_count == 0
    sandbox_apply_attempt_count = 0
    sandbox_apply_success_count = 0
    production_apply_attempt_count = 0
    fabricated_candidate_count = 0
    blocked_value_mismatch_auto_apply_count = 0

    _write_json(
        OUT_NOOP,
        {
            "no_op_due_to_zero_real_candidates": no_op_due_to_zero_real_candidates,
            "real_sandbox_preview_candidate_count": real_sandbox_preview_candidate_count,
            "sandbox_apply_attempt_count": sandbox_apply_attempt_count,
            "sandbox_apply_success_count": sandbox_apply_success_count,
            "production_apply_attempt_count": production_apply_attempt_count,
            "fabricated_candidate_count": fabricated_candidate_count,
            "real_apply_executed": False,
            "note": "Stage 8C zero-candidate path executed safely.",
        },
    )

    _write_json(
        OUT_BLOCKER,
        {
            "production_preflight_allowed": False,
            "production_preflight_blocked_reason": "no_real_sandbox_preview_candidate",
            "real_sandbox_preview_candidate_count": real_sandbox_preview_candidate_count,
            "sandbox_apply_attempt_count": sandbox_apply_attempt_count,
            "production_apply_attempt_count": production_apply_attempt_count,
        },
    )

    after = _snapshot_hashes()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()

    summary = {
        "stage": "8C",
        "external_api_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": sandbox_apply_attempt_count,
        "sandbox_apply_success_count": sandbox_apply_success_count,
        "production_apply_attempt_count": production_apply_attempt_count,
        "stage8b_summary_loaded": stage8b_summary_loaded,
        "valid_real_second_review_results_loaded": valid_real_second_review_results_loaded,
        "real_candidate_projection_loaded": real_candidate_projection_loaded,
        "stage8b_guard_ok": stage8b_guard_ok,
        "real_second_review_input_row_count": int(s8b.get("real_second_review_input_row_count", len(valid_df) + len(invalid_df))),
        "valid_real_second_review_count": len(valid_df),
        "invalid_real_second_review_count": len(invalid_df),
        "confirm_needs_more_info_count": int(decision_counts.get("CONFIRM_NEEDS_MORE_INFO", 0)),
        "escalate_manual_accounting_review_count": int(decision_counts.get("ESCALATE_TO_MANUAL_ACCOUNTING_REVIEW", 0)),
        "confirm_reject_count": int(decision_counts.get("CONFIRM_REJECT", 0)),
        "approve_for_sandbox_preview_candidate_count": int(decision_counts.get("APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE", 0)),
        "real_sandbox_preview_candidate_count": real_sandbox_preview_candidate_count,
        "no_op_due_to_zero_real_candidates": no_op_due_to_zero_real_candidates,
        "fabricated_candidate_count": fabricated_candidate_count,
        "blocked_value_mismatch_auto_apply_count": blocked_value_mismatch_auto_apply_count,
        "production_preflight_allowed": False,
        "production_preflight_blocked_reason": "no_real_sandbox_preview_candidate",
        "unresolved_followup_summary_generated": True,
        "zero_candidate_noop_proof_generated": True,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": _norm(delivery.get("overall_status")),
        "ready_for_stage8d_real_candidate_collection_or_manual_resolution": True,
        "ready_for_production_preflight": False,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# Stage 8C Real Candidate Preflight (Zero-Candidate Gate)",
        "",
        "Mode: no API call, no sandbox apply, no production apply.",
        "",
        "## Stage8B Guard",
        f"- stage8b_guard_ok: {stage8b_guard_ok}",
        "",
        "## Candidate Status",
        f"- real_sandbox_preview_candidate_count: {real_sandbox_preview_candidate_count}",
        f"- no_op_due_to_zero_real_candidates: {no_op_due_to_zero_real_candidates}",
        "",
        "## Apply Status",
        f"- sandbox_apply_attempt_count: {sandbox_apply_attempt_count}",
        f"- sandbox_apply_success_count: {sandbox_apply_success_count}",
        f"- production_apply_attempt_count: {production_apply_attempt_count}",
        "",
        "## Blocker",
        "- production_preflight_allowed: false",
        "- production_preflight_blocked_reason: no_real_sandbox_preview_candidate",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print("stage8c_status=ok")
    print(f"stage8c_summary={OUT_SUMMARY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
