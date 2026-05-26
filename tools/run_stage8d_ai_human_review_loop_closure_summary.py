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
OUT_BASE = BASE_DIR / "output"

SUMMARY_PATHS = {
    "7P": OUT_BASE / "stage7p_ai_suggestion_queue_integration" / "203_stage7p_ai_suggestion_queue_summary.json",
    "7Q": OUT_BASE / "stage7q_human_approval_flow_design" / "204_stage7q_human_approval_flow_summary.json",
    "7R": OUT_BASE / "stage7r_human_approval_sandbox_apply_preview" / "205_stage7r_sandbox_apply_preview_summary.json",
    "7S": OUT_BASE / "stage7s_blocked_approved_suggestion_review" / "206_stage7s_blocked_review_summary.json",
    "7T": OUT_BASE / "stage7t_real_human_approval_input_design" / "207_stage7t_real_human_approval_input_summary.json",
    "7U": OUT_BASE / "stage7u_real_human_approval_validation" / "208_stage7u_real_human_approval_validation_summary.json",
    "7V": OUT_BASE / "stage7v_sandbox_preview_from_validated_real_human_approval" / "209_stage7v_sandbox_preview_from_validated_approval_summary.json",
    "7W": OUT_BASE / "stage7w_second_review_needs_more_info_package" / "210_stage7w_second_review_summary.json",
    "7X": OUT_BASE / "stage7x_second_review_input_validation" / "211_stage7x_second_review_validation_summary.json",
    "7Y": OUT_BASE / "stage7y_sandbox_preview_candidate_preflight" / "212_stage7y_sandbox_preview_candidate_preflight_summary.json",
    "7Z": OUT_BASE / "stage7z_controlled_sample_exclusion_readiness_gate" / "213_stage7z_controlled_sample_exclusion_summary.json",
    "8A": OUT_BASE / "stage8a_real_second_review_input_intake_gate" / "214_stage8a_real_second_review_intake_summary.json",
    "8B": OUT_BASE / "stage8b_real_second_review_input_validation" / "215_stage8b_real_second_review_validation_summary.json",
    "8C": OUT_BASE / "stage8c_real_sandbox_preview_candidate_preflight" / "216_stage8c_real_candidate_preflight_summary.json",
}

OUT_DIR = OUT_BASE / "stage8d_ai_human_review_loop_closure_summary"
OUT_SUMMARY = OUT_DIR / "217_stage8d_ai_human_review_loop_closure_summary.json"
OUT_REPORT = OUT_DIR / "217_stage8d_ai_human_review_loop_closure_report.md"
OUT_TIMELINE = OUT_DIR / "217_stage8d_stage_timeline_audit.xlsx"
OUT_GATE_MATRIX = OUT_DIR / "217_stage8d_safety_gate_matrix.xlsx"
OUT_REMAINING = OUT_DIR / "217_stage8d_remaining_manual_actions.xlsx"
OUT_NO_APPLY = OUT_DIR / "217_stage8d_no_apply_proof.json"

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
    missing = [f"{k}:{v}" for k, v in SUMMARY_PATHS.items() if not v.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "8D",
                "external_api_called": False,
                "real_apply_executed": False,
                "blocked": True,
                "blocked_reason": f"missing_summaries:{'|'.join(missing)}",
            },
        )
        print("stage8d_status=blocked_missing_inputs")
        return 0

    before = _snapshot_hashes()
    summaries: Dict[str, Dict[str, Any]] = {k: _load_json(p) for k, p in SUMMARY_PATHS.items()}

    s7p = summaries["7P"]
    s7q = summaries["7Q"]
    s7r = summaries["7R"]
    s7s = summaries["7S"]
    s7t = summaries["7T"]
    s7u = summaries["7U"]
    s7v = summaries["7V"]
    s7w = summaries["7W"]
    s7x = summaries["7X"]
    s7y = summaries["7Y"]
    s7z = summaries["7Z"]
    s8a = summaries["8A"]
    s8b = summaries["8B"]
    s8c = summaries["8C"]

    # Safety-chain booleans
    stage8c_summary_loaded = True
    ai_suggestion_queue_integrated = int(s7p.get("integrated_ai_suggestion_count", 0)) > 0
    human_approval_required = int(s7p.get("requires_human_approval_count", 0)) == int(
        s7p.get("integrated_ai_suggestion_count", 0)
    )
    human_approval_not_safe_to_apply = bool(
        int(s7p.get("apply_allowed_count", 0)) == 0
        and s7q.get("real_apply_executed") is False
        and s7r.get("real_apply_executed") is False
    )
    value_mismatch_blocked = bool(
        int(s7r.get("value_mismatch_count", -1)) >= 2
        and int(s7r.get("blocked_apply_count", -1)) >= 2
        and int(s7s.get("apply_policy_correctly_blocked_count", -1)) >= 2
    )
    controlled_sample_excluded_from_production = bool(
        s7z.get("controlled_sample_candidate_excluded_from_production") is True
        and s7z.get("production_preflight_allowed") is False
    )
    real_second_review_input_validated = bool(
        s8a.get("real_second_review_input_present") is True
        and s8a.get("shallow_schema_check_pass") is True
        and s8b.get("real_second_review_input_schema_valid") is True
        and int(s8b.get("invalid_real_second_review_count", -1)) == 0
    )
    real_sandbox_preview_candidate_count = int(s8c.get("real_sandbox_preview_candidate_count", 0))
    production_preflight_allowed = bool(s8c.get("production_preflight_allowed") is True)
    production_preflight_blocked_reason = _norm(
        s8c.get("production_preflight_blocked_reason", "no_real_sandbox_preview_candidate")
    )

    remaining_needs_more_info_count = int(s8c.get("confirm_needs_more_info_count", 0))
    remaining_manual_accounting_escalation_count = int(s8c.get("escalate_manual_accounting_review_count", 0))

    timeline_rows: List[Dict[str, Any]] = []
    for sid in ["7P", "7Q", "7R", "7S", "7T", "7U", "7V", "7W", "7X", "7Y", "7Z", "8A", "8B", "8C"]:
        d = summaries[sid]
        timeline_rows.append(
            {
                "stage_id": sid,
                "stage_name": _norm(d.get("stage")),
                "external_api_called": d.get("external_api_called"),
                "real_apply_executed": d.get("real_apply_executed"),
                "check_delivery_state_overall_status": _norm(d.get("check_delivery_state_overall_status")),
                "production_files_modified": d.get("production_files_modified"),
                "official_02b_modified": d.get("official_02b_modified"),
                "formal_rules_modified": d.get("formal_rules_modified"),
                "standardizer_modified": d.get("standardizer_modified"),
                "release_package_modified": d.get("release_package_modified"),
            }
        )
    timeline_df = pd.DataFrame(timeline_rows)
    timeline_df.to_excel(OUT_TIMELINE, sheet_name="stage_timeline_audit", index=False, engine="openpyxl")

    gate_matrix_rows = [
        {
            "gate_name": "ai_suggestions_integrated",
            "status": ai_suggestion_queue_integrated,
            "evidence": f"stage7p_integrated_ai_suggestion_count={s7p.get('integrated_ai_suggestion_count')}",
        },
        {
            "gate_name": "human_approval_required",
            "status": human_approval_required,
            "evidence": f"stage7p_requires_human_approval_count={s7p.get('requires_human_approval_count')}",
        },
        {
            "gate_name": "human_approval_not_safe_to_apply",
            "status": human_approval_not_safe_to_apply,
            "evidence": "stage7p_apply_allowed_count=0; stage7q/7r real_apply_executed=false",
        },
        {
            "gate_name": "value_mismatch_blocked",
            "status": value_mismatch_blocked,
            "evidence": f"stage7r_blocked_apply_count={s7r.get('blocked_apply_count')}; stage7s_apply_policy_correctly_blocked_count={s7s.get('apply_policy_correctly_blocked_count')}",
        },
        {
            "gate_name": "controlled_sample_excluded_from_production",
            "status": controlled_sample_excluded_from_production,
            "evidence": f"stage7z_controlled_sample_candidate_excluded_from_production={s7z.get('controlled_sample_candidate_excluded_from_production')}",
        },
        {
            "gate_name": "real_second_review_input_validated",
            "status": real_second_review_input_validated,
            "evidence": f"stage8b_invalid_real_second_review_count={s8b.get('invalid_real_second_review_count')}",
        },
        {
            "gate_name": "zero_real_sandbox_candidates",
            "status": real_sandbox_preview_candidate_count == 0,
            "evidence": f"stage8c_real_sandbox_preview_candidate_count={real_sandbox_preview_candidate_count}",
        },
        {
            "gate_name": "production_preflight_blocked",
            "status": not production_preflight_allowed,
            "evidence": f"stage8c_blocked_reason={production_preflight_blocked_reason}",
        },
    ]
    gate_df = pd.DataFrame(gate_matrix_rows)
    gate_df.to_excel(OUT_GATE_MATRIX, sheet_name="safety_gate_matrix", index=False, engine="openpyxl")

    remaining_rows = [
        {
            "action_type": "needs_more_info",
            "count": remaining_needs_more_info_count,
            "next_action": "collect_additional_evidence_and_re-review",
        },
        {
            "action_type": "manual_accounting_escalation",
            "count": remaining_manual_accounting_escalation_count,
            "next_action": "manual_accounting_resolution_required",
        },
        {"action_type": "confirm_reject", "count": int(s8c.get("confirm_reject_count", 0)), "next_action": "keep_rejected"},
        {
            "action_type": "real_sandbox_preview_candidates",
            "count": real_sandbox_preview_candidate_count,
            "next_action": "none_currently",
        },
    ]
    remaining_df = pd.DataFrame(remaining_rows)
    remaining_df.to_excel(OUT_REMAINING, sheet_name="remaining_manual_actions", index=False, engine="openpyxl")

    _write_json(
        OUT_NO_APPLY,
        {
            "external_api_called": False,
            "real_apply_executed": False,
            "sandbox_apply_attempt_count": 0,
            "sandbox_apply_success_count": 0,
            "production_apply_attempt_count": 0,
            "production_apply_success_count": 0,
            "note": "Stage 8D is documentation/audit only.",
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
        "stage": "8D",
        "external_api_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "stage8c_summary_loaded": stage8c_summary_loaded,
        "ai_suggestion_queue_integrated": ai_suggestion_queue_integrated,
        "human_approval_required": human_approval_required,
        "human_approval_not_safe_to_apply": human_approval_not_safe_to_apply,
        "value_mismatch_blocked": value_mismatch_blocked,
        "controlled_sample_excluded_from_production": controlled_sample_excluded_from_production,
        "real_second_review_input_validated": real_second_review_input_validated,
        "real_sandbox_preview_candidate_count": real_sandbox_preview_candidate_count,
        "production_preflight_allowed": production_preflight_allowed,
        "production_preflight_blocked_reason": production_preflight_blocked_reason,
        "remaining_needs_more_info_count": remaining_needs_more_info_count,
        "remaining_manual_accounting_escalation_count": remaining_manual_accounting_escalation_count,
        "closure_report_generated": True,
        "remaining_manual_actions_generated": True,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": _norm(delivery.get("overall_status")),
        "ready_for_future_real_candidate_collection": True,
        "ready_for_production_preflight": False,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# Stage 8D AI-Human Review Loop Closure Summary",
        "",
        "Mode: documentation/audit only. No API calls, no apply.",
        "",
        "## End-to-End Safety Chain",
        f"- AI suggestions entered queue: {ai_suggestion_queue_integrated}",
        f"- All AI suggestions required human approval: {human_approval_required}",
        f"- Human approval did not imply safe_to_apply: {human_approval_not_safe_to_apply}",
        f"- Value mismatch suggestions were blocked: {value_mismatch_blocked}",
        f"- Controlled sample candidate excluded from production: {controlled_sample_excluded_from_production}",
        f"- Real second-review input validated: {real_second_review_input_validated}",
        f"- Real sandbox preview candidate count: {real_sandbox_preview_candidate_count}",
        f"- Production preflight allowed: {production_preflight_allowed}",
        f"- Production blocker: {production_preflight_blocked_reason}",
        "",
        "## Remaining Manual Actions",
        f"- needs_more_info: {remaining_needs_more_info_count}",
        f"- manual_accounting_escalation: {remaining_manual_accounting_escalation_count}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print("stage8d_status=ok")
    print(f"stage8d_summary={OUT_SUMMARY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
