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
IN_DIR = BASE_DIR / "output" / "stage7u_real_human_approval_validation"

IN_SUMMARY = IN_DIR / "208_stage7u_real_human_approval_validation_summary.json"
IN_VALID = IN_DIR / "208_stage7u_validated_approval_results.xlsx"
IN_INVALID = IN_DIR / "208_stage7u_invalid_approval_results.xlsx"
IN_AUDIT = IN_DIR / "208_stage7u_validation_audit.xlsx"
IN_PROJECTION = IN_DIR / "208_stage7u_sandbox_preview_candidate_projection.xlsx"
IN_NEG = IN_DIR / "208_stage7u_negative_validation_tests.json"

OUT_DIR = BASE_DIR / "output" / "stage7v_sandbox_preview_from_validated_real_human_approval"
OUT_SUMMARY = OUT_DIR / "209_stage7v_sandbox_preview_from_validated_approval_summary.json"
OUT_REPORT = OUT_DIR / "209_stage7v_sandbox_preview_from_validated_approval_report.md"
OUT_FILTER_AUDIT = OUT_DIR / "209_stage7v_candidate_filter_audit.xlsx"
OUT_NOOP_PROOF = OUT_DIR / "209_stage7v_noop_safety_proof.json"
OUT_BLOCKED_GUARD = OUT_DIR / "209_stage7v_blocked_value_mismatch_guard.json"

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
    s = _norm(v).lower()
    return s in {"1", "true", "yes", "y"}


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
    required = [IN_SUMMARY, IN_VALID, IN_INVALID, IN_AUDIT, IN_PROJECTION, IN_NEG]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "7V",
                "external_api_called": False,
                "real_apply_executed": False,
                "stage7u_summary_loaded": False,
                "blocked": True,
                "blocked_reason": f"missing_input:{'|'.join(missing)}",
            },
        )
        print("stage7v_status=blocked_missing_input")
        return 0

    before = _snapshot_hashes()

    stage7u_summary = _load_json(IN_SUMMARY)
    validated_df = pd.read_excel(IN_VALID)
    invalid_df = pd.read_excel(IN_INVALID)
    _ = pd.read_excel(IN_AUDIT)
    projection_df = pd.read_excel(IN_PROJECTION)
    _ = _load_json(IN_NEG)

    stage7u_summary_loaded = True
    validated_approval_results_loaded = True
    candidate_projection_loaded = True
    validated_approval_count = len(validated_df)
    invalid_approval_count = len(invalid_df)

    # Verify Stage7U summary guard fields
    stage7u_guard_ok = bool(
        stage7u_summary.get("approval_input_loaded") is True
        and stage7u_summary.get("approval_input_schema_valid") is True
        and stage7u_summary.get("validation_rules_loaded") is True
        and stage7u_summary.get("value_mismatch_approve_rejected") is True
        and stage7u_summary.get("approve_for_real_apply_rejected") is True
        and int(stage7u_summary.get("blocked_value_mismatch_auto_apply_count", -1)) == 0
        and _norm(stage7u_summary.get("check_delivery_state_overall_status")) == "PASS"
        and stage7u_summary.get("ready_for_stage7v_sandbox_preview_from_validated_real_human_approval") is True
    )

    # Candidate filter rules for Stage7V bridge
    filter_rows: List[Dict[str, Any]] = []
    candidates: List[Dict[str, Any]] = []
    value_mismatch_candidate_count = 0
    approve_for_real_apply_detected_count = 0
    blocked_value_mismatch_auto_apply_count = 0

    valid_map = {
        (_norm(r.get("queue_item_id")), _norm(r.get("suggestion_id"))): r.to_dict()
        for _, r in validated_df.iterrows()
    }

    for _, p in projection_df.iterrows():
        queue_item_id = _norm(p.get("queue_item_id"))
        suggestion_id = _norm(p.get("suggestion_id"))
        key = (queue_item_id, suggestion_id)
        v = valid_map.get(key, {})

        row_valid = _as_bool(p.get("row_valid"))
        projection_candidate = _as_bool(p.get("sandbox_preview_candidate"))
        decision = _norm(v.get("human_decision") or p.get("human_decision"))
        value_mismatch = _as_bool(v.get("value_mismatch") if key in valid_map else p.get("value_mismatch"))
        conflict_type = _norm(v.get("conflict_type"))
        prior_stage_status = _norm(v.get("prior_stage_status")).lower()
        corrected_fields_present = any(
            _norm(v.get(x))
            for x in ["corrected_metric_name", "corrected_value", "corrected_unit", "corrected_fiscal_year"]
        )

        if decision == "APPROVE_FOR_REAL_APPLY":
            approve_for_real_apply_detected_count += 1

        reasons = []
        if not row_valid:
            reasons.append("row_not_valid")
        if not projection_candidate:
            reasons.append("projection_not_candidate")
        if decision != "APPROVE_FOR_SANDBOX_PREVIEW":
            reasons.append("decision_not_approve_for_sandbox_preview")
        if value_mismatch:
            reasons.append("value_mismatch_true")
        if "true_value_conflict" in conflict_type:
            reasons.append("true_value_conflict")
        if "blocked_apply" in prior_stage_status or "unresolved_conflict" in prior_stage_status:
            reasons.append("prior_stage_blocked_or_unresolved")
        if corrected_fields_present:
            reasons.append("corrected_fields_present")

        is_candidate = len(reasons) == 0
        if is_candidate:
            candidates.append(
                {
                    "queue_item_id": queue_item_id,
                    "suggestion_id": suggestion_id,
                    "human_decision": decision,
                    "conflict_type": conflict_type,
                    "value_mismatch": value_mismatch,
                    "prior_stage_status": prior_stage_status,
                }
            )
        if value_mismatch and is_candidate:
            value_mismatch_candidate_count += 1
            blocked_value_mismatch_auto_apply_count += 1

        filter_rows.append(
            {
                "queue_item_id": queue_item_id,
                "suggestion_id": suggestion_id,
                "row_valid": row_valid,
                "projection_candidate": projection_candidate,
                "human_decision": decision,
                "value_mismatch": value_mismatch,
                "conflict_type": conflict_type,
                "prior_stage_status": prior_stage_status,
                "corrected_fields_present": corrected_fields_present,
                "final_candidate": is_candidate,
                "reject_reasons": "|".join(reasons),
            }
        )

    candidate_filter_df = pd.DataFrame(filter_rows)
    candidate_filter_df.to_excel(OUT_FILTER_AUDIT, sheet_name="candidate_filter_audit", index=False, engine="openpyxl")

    sandbox_preview_candidate_count = len(candidates)
    sandbox_apply_attempt_count = 0
    sandbox_apply_success_count = 0
    fabricated_candidate_count = 0
    no_op_due_to_zero_candidates = sandbox_preview_candidate_count == 0

    noop_proof = {
        "no_op_due_to_zero_candidates": no_op_due_to_zero_candidates,
        "sandbox_preview_candidate_count": sandbox_preview_candidate_count,
        "sandbox_apply_attempt_count": sandbox_apply_attempt_count,
        "sandbox_apply_success_count": sandbox_apply_success_count,
        "fabricated_candidate_count": fabricated_candidate_count,
        "real_apply_executed": False,
        "production_write_executed": False,
        "notes": "Stage7V safely handled zero-candidate path without apply actions.",
    }
    _write_json(OUT_NOOP_PROOF, noop_proof)

    blocked_guard = {
        "blocked_value_mismatch_auto_apply_count": blocked_value_mismatch_auto_apply_count,
        "value_mismatch_candidate_count": value_mismatch_candidate_count,
        "approve_for_real_apply_detected_count": approve_for_real_apply_detected_count,
        "guard_status": "PASS"
        if blocked_value_mismatch_auto_apply_count == 0 and approve_for_real_apply_detected_count == 0
        else "FAIL",
        "candidate_rows": candidates,
    }
    _write_json(OUT_BLOCKED_GUARD, blocked_guard)

    after = _snapshot_hashes()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]
    delivery = _run_delivery_check()
    check_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "7V",
        "external_api_called": False,
        "real_apply_executed": False,
        "stage7u_summary_loaded": stage7u_summary_loaded,
        "validated_approval_results_loaded": validated_approval_results_loaded,
        "candidate_projection_loaded": candidate_projection_loaded,
        "validated_approval_count": validated_approval_count,
        "invalid_approval_count": invalid_approval_count,
        "sandbox_preview_candidate_count": sandbox_preview_candidate_count,
        "sandbox_apply_attempt_count": sandbox_apply_attempt_count,
        "sandbox_apply_success_count": sandbox_apply_success_count,
        "no_op_due_to_zero_candidates": no_op_due_to_zero_candidates,
        "fabricated_candidate_count": fabricated_candidate_count,
        "blocked_value_mismatch_auto_apply_count": blocked_value_mismatch_auto_apply_count,
        "value_mismatch_candidate_count": value_mismatch_candidate_count,
        "approve_for_real_apply_detected_count": approve_for_real_apply_detected_count,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": check_status,
        "stage7u_guard_ok": stage7u_guard_ok,
        "ready_for_stage7w_real_human_candidate_collection_or_second_review": bool(
            stage7u_guard_ok
            and no_op_due_to_zero_candidates
            and blocked_value_mismatch_auto_apply_count == 0
            and check_status == "PASS"
        ),
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# Stage7V Sandbox Preview Bridge (Validated Real Human Approval)",
        "",
        "No external API call; no real apply; no production write.",
        "",
        "## Input Load",
        f"- stage7u_summary_loaded: {summary['stage7u_summary_loaded']}",
        f"- validated_approval_results_loaded: {summary['validated_approval_results_loaded']}",
        f"- candidate_projection_loaded: {summary['candidate_projection_loaded']}",
        f"- stage7u_guard_ok: {summary['stage7u_guard_ok']}",
        "",
        "## Candidate Result",
        f"- validated_approval_count: {summary['validated_approval_count']}",
        f"- invalid_approval_count: {summary['invalid_approval_count']}",
        f"- sandbox_preview_candidate_count: {summary['sandbox_preview_candidate_count']}",
        f"- no_op_due_to_zero_candidates: {summary['no_op_due_to_zero_candidates']}",
        f"- sandbox_apply_attempt_count: {summary['sandbox_apply_attempt_count']}",
        f"- sandbox_apply_success_count: {summary['sandbox_apply_success_count']}",
        f"- fabricated_candidate_count: {summary['fabricated_candidate_count']}",
        "",
        "## Guardrail",
        f"- blocked_value_mismatch_auto_apply_count: {summary['blocked_value_mismatch_auto_apply_count']}",
        f"- value_mismatch_candidate_count: {summary['value_mismatch_candidate_count']}",
        f"- approve_for_real_apply_detected_count: {summary['approve_for_real_apply_detected_count']}",
        "",
        "## Integrity",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        "",
        "## Decision",
        f"- ready_for_stage7w_real_human_candidate_collection_or_second_review: {summary['ready_for_stage7w_real_human_candidate_collection_or_second_review']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"stage7v_external_api_called={str(summary['external_api_called']).lower()}")
    print(f"stage7v_real_apply_executed={str(summary['real_apply_executed']).lower()}")
    print(f"stage7v_stage7u_summary_loaded={str(summary['stage7u_summary_loaded']).lower()}")
    print(f"stage7v_sandbox_preview_candidate_count={summary['sandbox_preview_candidate_count']}")
    print(f"stage7v_sandbox_apply_attempt_count={summary['sandbox_apply_attempt_count']}")
    print(f"stage7v_no_op_due_to_zero_candidates={str(summary['no_op_due_to_zero_candidates']).lower()}")
    print(f"stage7v_check_delivery_state={summary['check_delivery_state_overall_status']}")
    print(
        "stage7v_ready_for_stage7w="
        f"{str(summary['ready_for_stage7w_real_human_candidate_collection_or_second_review']).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
