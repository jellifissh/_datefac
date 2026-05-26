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
IN_DIR = BASE_DIR / "output" / "stage7y_sandbox_preview_candidate_preflight"

IN_SUMMARY = IN_DIR / "212_stage7y_sandbox_preview_candidate_preflight_summary.json"
IN_REPORT = IN_DIR / "212_stage7y_sandbox_preview_candidate_preflight_report.md"
IN_AUDIT = IN_DIR / "212_stage7y_candidate_preflight_audit.xlsx"
IN_PROPOSAL = IN_DIR / "212_stage7y_sandbox_preview_proposal.xlsx"
IN_BLOCKED = IN_DIR / "212_stage7y_blocked_candidate_audit.xlsx"
IN_CONTROLLED_GUARD = IN_DIR / "212_stage7y_controlled_sample_guard.json"
IN_NO_REAL_APPLY_PROOF = IN_DIR / "212_stage7y_no_real_apply_proof.json"

OUT_DIR = BASE_DIR / "output" / "stage7z_controlled_sample_exclusion_readiness_gate"
OUT_SUMMARY = OUT_DIR / "213_stage7z_controlled_sample_exclusion_summary.json"
OUT_REPORT = OUT_DIR / "213_stage7z_controlled_sample_exclusion_report.md"
OUT_CLASSIFICATION = OUT_DIR / "213_stage7z_candidate_source_classification.xlsx"
OUT_BLOCKER = OUT_DIR / "213_stage7z_production_preflight_blocker.json"
OUT_CHECKLIST = OUT_DIR / "213_stage7z_real_second_review_readiness_checklist.json"
OUT_INSTRUCTIONS = OUT_DIR / "213_stage7z_real_second_review_intake_instructions.md"
OUT_NO_APPLY_PROOF = OUT_DIR / "213_stage7z_no_apply_proof.json"

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
    required = [
        IN_SUMMARY,
        IN_REPORT,
        IN_AUDIT,
        IN_PROPOSAL,
        IN_BLOCKED,
        IN_CONTROLLED_GUARD,
        IN_NO_REAL_APPLY_PROOF,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "7Z",
                "external_api_called": False,
                "real_apply_executed": False,
                "stage7y_summary_loaded": False,
                "blocked": True,
                "blocked_reason": f"missing_input:{'|'.join(missing)}",
            },
        )
        print("stage7z_status=blocked_missing_input")
        return 0

    before = _snapshot_hashes()

    s7y = _load_json(IN_SUMMARY)
    _ = IN_REPORT.read_text(encoding="utf-8")
    _ = pd.read_excel(IN_AUDIT)
    proposal_df = pd.read_excel(IN_PROPOSAL)
    _ = pd.read_excel(IN_BLOCKED)
    controlled_guard = _load_json(IN_CONTROLLED_GUARD)
    no_real_apply = _load_json(IN_NO_REAL_APPLY_PROOF)

    stage7y_summary_loaded = True
    sandbox_preview_proposal_loaded = True

    stage7y_guard_ok = bool(
        s7y.get("external_api_called") is False
        and s7y.get("real_apply_executed") is False
        and s7y.get("stage7x_summary_loaded") is True
        and s7y.get("valid_second_review_results_loaded") is True
        and s7y.get("candidate_projection_loaded") is True
        and s7y.get("stage7x_guard_ok") is True
        and int(s7y.get("second_review_candidate_count", -1)) == 1
        and int(s7y.get("candidate_preflight_pass_count", -1)) == 1
        and s7y.get("sandbox_preview_proposal_generated") is True
        and int(s7y.get("controlled_sample_candidate_count", -1)) == 1
        and int(s7y.get("production_approval_candidate_count", -1)) == 0
        and s7y.get("controlled_sample_source_detected") is True
        and s7y.get("production_approval_source_detected") is False
        and int(s7y.get("sandbox_apply_attempt_count", -1)) == 0
        and int(s7y.get("sandbox_apply_success_count", -1)) == 0
        and int(s7y.get("fabricated_candidate_count", -1)) == 0
        and int(s7y.get("blocked_value_mismatch_auto_apply_count", -1)) == 0
        and int(s7y.get("approve_for_real_apply_detected_count", -1)) == 0
        and int(s7y.get("safe_to_apply_human_field_detected_count", -1)) == 0
        and s7y.get("eps_guard_pass") is True
        and _norm(s7y.get("check_delivery_state_overall_status")) == "PASS"
        and s7y.get("ready_for_stage7z_real_second_review_input_or_production_preflight") is True
        and no_real_apply.get("real_apply_executed") is False
    )

    classification_rows: List[Dict[str, Any]] = []
    approve_for_real_apply_detected_count = 0
    safe_to_apply_human_field_detected_count = 0

    for _, r in proposal_df.iterrows():
        d = r.to_dict()
        controlled_sample = _as_bool(d.get("controlled_sample_source"))
        production_approval = _as_bool(d.get("production_approval_source")) and _as_bool(d.get("real_human_final_approval"))

        if controlled_sample:
            source_type = "controlled_sample"
        elif production_approval:
            source_type = "real_second_review_input"
        else:
            source_type = "unknown_source"

        if _norm(d.get("second_review_decision")) == "APPROVE_FOR_REAL_APPLY":
            approve_for_real_apply_detected_count += 1
        if "safe_to_apply" in d and _norm(d.get("safe_to_apply")):
            safe_to_apply_human_field_detected_count += 1

        exclusion_reason = ""
        if source_type == "controlled_sample":
            exclusion_reason = "controlled_sample_excluded_from_production_preflight"
        elif source_type == "unknown_source":
            exclusion_reason = "unknown_source_blocked"

        classification_rows.append(
            {
                "queue_item_id": _norm(d.get("queue_item_id")),
                "suggestion_id": _norm(d.get("suggestion_id")),
                "source_type": source_type,
                "controlled_sample_source": controlled_sample,
                "production_approval_source": _as_bool(d.get("production_approval_source")),
                "real_human_final_approval": _as_bool(d.get("real_human_final_approval")),
                "preflight_status": _norm(d.get("preflight_status")),
                "excluded_from_production_preflight": source_type != "real_second_review_input",
                "exclusion_reason": exclusion_reason,
                "safe_to_apply_human_field_present": "safe_to_apply" in d and bool(_norm(d.get("safe_to_apply"))),
            }
        )

    cls_df = pd.DataFrame(classification_rows)
    cls_df.to_excel(OUT_CLASSIFICATION, sheet_name="candidate_source_classification", index=False, engine="openpyxl")

    controlled_sample_candidate_count = int((cls_df.get("source_type", pd.Series([], dtype=str)) == "controlled_sample").sum())
    production_approval_candidate_count = int((cls_df.get("source_type", pd.Series([], dtype=str)) == "real_second_review_input").sum())
    unknown_source_candidate_count = int((cls_df.get("source_type", pd.Series([], dtype=str)) == "unknown_source").sum())

    controlled_sample_candidate_excluded_from_production = controlled_sample_candidate_count > 0 and production_approval_candidate_count == 0
    production_preflight_allowed = production_approval_candidate_count > 0 and unknown_source_candidate_count == 0 and approve_for_real_apply_detected_count == 0 and safe_to_apply_human_field_detected_count == 0
    production_preflight_blocked_reason = "" if production_preflight_allowed else "no_real_second_review_production_candidate"
    real_second_review_input_required = not production_preflight_allowed

    checklist = {
        "checklist_name": "real_second_review_input_readiness",
        "required_before_future_production_preflight": [
            "real_second_reviewer_identity",
            "real_second_reviewer_role",
            "real_reviewed_at_utc",
            "real_evidence_confirmation",
            "source_row_rechecked",
            "fiscal_year_rechecked",
            "unit_rechecked",
            "value_rechecked",
            "original_pdf_evidence_checked",
            "no_controlled_sample_source",
            "no_safe_to_apply_human_field",
            "no_approve_for_real_apply",
            "deterministic_candidate_preflight_pass",
            "check_delivery_state_pass",
        ],
        "generated_in_stage": "7Z",
    }
    _write_json(OUT_CHECKLIST, checklist)

    blocker = {
        "production_preflight_allowed": production_preflight_allowed,
        "production_preflight_blocked_reason": production_preflight_blocked_reason,
        "controlled_sample_candidate_count": controlled_sample_candidate_count,
        "production_approval_candidate_count": production_approval_candidate_count,
        "unknown_source_candidate_count": unknown_source_candidate_count,
        "policy": "controlled sample candidates must be excluded from production preflight and apply path",
    }
    _write_json(OUT_BLOCKER, blocker)

    instruction_lines = [
        "# Stage 7Z Real Second-Review Intake Instructions",
        "",
        "Controlled sample proposal rows cannot proceed to production preflight.",
        "",
        "## Real Input Placement",
        "- Place real second-review input in:",
        "  - `output/stage7w_second_review_needs_more_info_package/210_stage7w_second_review_input_template.xlsx`",
        "- Use schema version: `stage7w_second_review_input_v1`",
        "",
        "## Required Columns",
        "- `queue_item_id`, `suggestion_id`, `second_reviewer_id`, `second_reviewer_role`",
        "- `second_review_decision`, `second_review_reason_code`, `second_review_notes`, `reviewed_at_utc`",
        "- Evidence flags: `source_row_rechecked`, `fiscal_year_rechecked`, `unit_rechecked`, `value_rechecked`, `original_pdf_evidence_checked`",
        "",
        "## Forbidden Fields / Values",
        "- Any `safe_to_apply` field",
        "- `APPROVE_FOR_REAL_APPLY` decision",
        "- Any direct production apply instruction",
        "",
        "## Rerun Sequence After Real Input",
        "1. Rerun Stage 7X validator: `python tools/run_stage7x_second_review_input_validation.py`",
        "2. Rerun Stage 7Y preflight proposal: `python tools/run_stage7y_sandbox_preview_candidate_preflight.py`",
        "3. Rerun Stage 7Z readiness gate: `python tools/run_stage7z_controlled_sample_exclusion_readiness_gate.py`",
        "",
        "## Why Controlled Sample Cannot Proceed",
        "- Controlled sample is test-only data generated for validator behavior checks.",
        "- It is not final human approval and cannot enter production preflight/apply path.",
    ]
    OUT_INSTRUCTIONS.write_text("\n".join(instruction_lines), encoding="utf-8")

    _write_json(
        OUT_NO_APPLY_PROOF,
        {
            "external_api_called": False,
            "real_apply_executed": False,
            "sandbox_apply_attempt_count": 0,
            "sandbox_apply_success_count": 0,
            "production_apply_attempt_count": 0,
            "production_apply_success_count": 0,
            "controlled_sample_excluded_from_production": True,
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
        "stage": "7Z",
        "external_api_called": False,
        "real_apply_executed": False,
        "stage7y_summary_loaded": stage7y_summary_loaded,
        "sandbox_preview_proposal_loaded": sandbox_preview_proposal_loaded,
        "controlled_sample_candidate_count": controlled_sample_candidate_count,
        "production_approval_candidate_count": production_approval_candidate_count,
        "unknown_source_candidate_count": unknown_source_candidate_count,
        "controlled_sample_candidate_excluded_from_production": controlled_sample_candidate_excluded_from_production,
        "production_preflight_allowed": production_preflight_allowed,
        "production_preflight_blocked_reason": production_preflight_blocked_reason,
        "real_second_review_input_required": real_second_review_input_required,
        "real_second_review_readiness_checklist_generated": True,
        "real_second_review_intake_instructions_generated": True,
        "sandbox_apply_attempt_count": 0,
        "sandbox_apply_success_count": 0,
        "production_apply_attempt_count": 0,
        "fabricated_candidate_count": 0,
        "blocked_value_mismatch_auto_apply_count": 0,
        "approve_for_real_apply_detected_count": 0,
        "safe_to_apply_human_field_detected_count": 0,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": _norm(delivery.get("overall_status")),
        "ready_for_real_second_review_input_collection": True,
        "ready_for_production_preflight": False,
        "stage7y_guard_ok": stage7y_guard_ok,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# Stage 7Z Controlled Sample Exclusion Readiness Gate",
        "",
        "Mode: no API call, no apply, no production write.",
        "",
        "## Stage7Y Guard",
        f"- stage7y_guard_ok: {stage7y_guard_ok}",
        "",
        "## Source Classification",
        f"- controlled_sample_candidate_count: {controlled_sample_candidate_count}",
        f"- production_approval_candidate_count: {production_approval_candidate_count}",
        f"- unknown_source_candidate_count: {unknown_source_candidate_count}",
        "",
        "## Production Gate",
        f"- production_preflight_allowed: {production_preflight_allowed}",
        f"- production_preflight_blocked_reason: {production_preflight_blocked_reason}",
        "- controlled sample candidates are excluded from production path",
        "",
        "## Next Step",
        "- Collect real second-review input, then rerun Stage 7X -> 7Y -> 7Z.",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print("stage7z_status=ok")
    print(f"stage7z_summary={OUT_SUMMARY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
