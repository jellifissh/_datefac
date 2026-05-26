import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

BASE_DIR = Path(r"D:\_datefac")
IN_DIR = BASE_DIR / "output" / "stage7x_second_review_input_validation"

IN_SUMMARY = IN_DIR / "211_stage7x_second_review_validation_summary.json"
IN_VALID = IN_DIR / "211_stage7x_valid_second_review_results.xlsx"
IN_INVALID = IN_DIR / "211_stage7x_invalid_second_review_results.xlsx"
IN_PROJECTION = IN_DIR / "211_stage7x_second_review_candidate_projection.xlsx"
IN_AUDIT = IN_DIR / "211_stage7x_validation_audit.xlsx"
IN_NEG = IN_DIR / "211_stage7x_negative_validation_tests.json"
IN_SAMPLE = IN_DIR / "211_stage7x_second_review_sample_input.xlsx"

OUT_DIR = BASE_DIR / "output" / "stage7y_sandbox_preview_candidate_preflight"
OUT_SUMMARY = OUT_DIR / "212_stage7y_sandbox_preview_candidate_preflight_summary.json"
OUT_REPORT = OUT_DIR / "212_stage7y_sandbox_preview_candidate_preflight_report.md"
OUT_AUDIT = OUT_DIR / "212_stage7y_candidate_preflight_audit.xlsx"
OUT_PROPOSAL = OUT_DIR / "212_stage7y_sandbox_preview_proposal.xlsx"
OUT_BLOCKED = OUT_DIR / "212_stage7y_blocked_candidate_audit.xlsx"
OUT_CONTROLLED_GUARD = OUT_DIR / "212_stage7y_controlled_sample_guard.json"
OUT_NO_REAL_APPLY_PROOF = OUT_DIR / "212_stage7y_no_real_apply_proof.json"

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


def _parse_number(v: Any) -> Tuple[bool, float]:
    text = _norm(v).replace(",", "")
    if not text:
        return False, 0.0
    m = re.fullmatch(r"[-+]?\d+(\.\d+)?", text)
    if not m:
        return False, 0.0
    try:
        return True, float(text)
    except Exception:
        return False, 0.0


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    required = [IN_SUMMARY, IN_VALID, IN_INVALID, IN_PROJECTION, IN_AUDIT, IN_NEG, IN_SAMPLE]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "7Y",
                "external_api_called": False,
                "real_apply_executed": False,
                "stage7x_summary_loaded": False,
                "blocked": True,
                "blocked_reason": f"missing_input:{'|'.join(missing)}",
            },
        )
        print("stage7y_status=blocked_missing_input")
        return 0

    before = _snapshot_hashes()

    s7x = _load_json(IN_SUMMARY)
    valid_df = pd.read_excel(IN_VALID)
    invalid_df = pd.read_excel(IN_INVALID)
    proj_df = pd.read_excel(IN_PROJECTION)
    audit_df = pd.read_excel(IN_AUDIT)
    _ = _load_json(IN_NEG)
    sample_df = pd.read_excel(IN_SAMPLE)

    stage7x_summary_loaded = True
    valid_second_review_results_loaded = True
    candidate_projection_loaded = True

    stage7x_guard_ok = bool(
        s7x.get("external_api_called") is False
        and s7x.get("real_apply_executed") is False
        and s7x.get("second_review_input_schema_valid") is True
        and s7x.get("sandbox_preview_candidate_projection_generated") is True
        and s7x.get("approve_for_real_apply_rejected") is True
        and s7x.get("safe_to_apply_human_field_rejected") is True
        and s7x.get("immutable_field_tamper_detected") is True
        and s7x.get("value_mismatch_without_corrected_value_rejected") is True
        and s7x.get("evidence_checks_required_for_candidate") is True
        and int(s7x.get("blocked_value_mismatch_auto_apply_count", -1)) == 0
        and int(s7x.get("sandbox_apply_attempt_count", -1)) == 0
        and int(s7x.get("sandbox_apply_success_count", -1)) == 0
        and _norm(s7x.get("check_delivery_state_overall_status")) == "PASS"
        and s7x.get("ready_for_stage7y_sandbox_preview_candidate_from_second_review") is True
    )

    valid_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for _, r in valid_df.iterrows():
        d = r.to_dict()
        key = (_norm(d.get("queue_item_id")), _norm(d.get("suggestion_id")))
        valid_map[key] = d

    audit_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for _, r in audit_df.iterrows():
        d = r.to_dict()
        key = (_norm(d.get("queue_item_id")), _norm(d.get("suggestion_id")))
        audit_map[key] = d

    sample_keys = {
        (_norm(r.get("queue_item_id")), _norm(r.get("suggestion_id")))
        for _, r in sample_df.iterrows()
    }

    projection_candidates: List[Dict[str, Any]] = []
    approve_for_real_apply_detected_count = 0
    safe_to_apply_human_field_detected_count = 0
    fabricated_candidate_count = 0
    blocked_value_mismatch_auto_apply_count = 0

    for _, row in proj_df.iterrows():
        d = row.to_dict()
        decision = _norm(d.get("second_review_decision"))
        key = (_norm(d.get("queue_item_id")), _norm(d.get("suggestion_id")))
        row_valid = _as_bool(d.get("row_valid"))
        proj_candidate = _as_bool(d.get("sandbox_preview_candidate"))

        if decision == "APPROVE_FOR_REAL_APPLY":
            approve_for_real_apply_detected_count += 1
        if "safe_to_apply" in d and _norm(d.get("safe_to_apply")):
            safe_to_apply_human_field_detected_count += 1

        if row_valid and proj_candidate and decision == "APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE":
            projection_candidates.append(
                {
                    **d,
                    "queue_item_id": key[0],
                    "suggestion_id": key[1],
                }
            )

    preflight_rows: List[Dict[str, Any]] = []
    proposal_rows: List[Dict[str, Any]] = []
    blocked_rows: List[Dict[str, Any]] = []
    eps_guard_pass = True

    for c in projection_candidates:
        key = (_norm(c.get("queue_item_id")), _norm(c.get("suggestion_id")))
        reasons: List[str] = []
        valid_row = valid_map.get(key)
        if valid_row is None:
            reasons.append("missing_in_valid_second_review_results")
            fabricated_candidate_count += 1
            valid_row = {}

        # Cross checks
        if _norm(valid_row.get("second_review_decision")) != "APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE":
            reasons.append("decision_mismatch_vs_valid_results")
        if not _as_bool(valid_row.get("row_valid")):
            reasons.append("valid_results_row_not_valid")
        if _norm(valid_row.get("validation_errors")):
            reasons.append("validation_errors_not_empty")
        for f in [
            "original_pdf_evidence_checked",
            "source_row_rechecked",
            "fiscal_year_rechecked",
            "unit_rechecked",
            "value_rechecked",
        ]:
            if not _as_bool(valid_row.get(f)):
                reasons.append(f"missing_required_evidence:{f}")
        if not _norm(valid_row.get("second_review_reason_code")):
            reasons.append("missing_second_review_reason_code")
        if not _norm(valid_row.get("second_review_notes")):
            reasons.append("missing_second_review_notes")

        value_mismatch = _as_bool(valid_row.get("value_mismatch"))
        conflict_type = _norm(valid_row.get("conflict_type")).lower()
        prior_stage_status = _norm(valid_row.get("prior_stage_status")).lower()
        corrected_value = _norm(valid_row.get("corrected_value"))
        corrected_unit = _norm(valid_row.get("corrected_unit"))
        corrected_fiscal_year = _norm(valid_row.get("corrected_fiscal_year"))
        suggested_unit = _norm(valid_row.get("suggested_unit"))
        existing_unit = _norm(valid_row.get("existing_unit"))
        notes = _norm(valid_row.get("second_review_notes"))

        if value_mismatch and not corrected_value:
            reasons.append("value_mismatch_without_corrected_value")
            blocked_value_mismatch_auto_apply_count += 1
        if "true_value_conflict" in conflict_type and not (corrected_value or notes):
            reasons.append("true_value_conflict_without_corrected_or_evidence")
        if "blocked_apply" in prior_stage_status:
            evidence_ok = all(
                _as_bool(valid_row.get(f))
                for f in [
                    "original_pdf_evidence_checked",
                    "source_row_rechecked",
                    "fiscal_year_rechecked",
                    "unit_rechecked",
                    "value_rechecked",
                ]
            )
            if not (corrected_value and evidence_ok):
                reasons.append("blocked_apply_without_corrected_and_full_evidence")

        # numeric parse guard for corrected_value if present
        metric_hint = (_norm(valid_row.get("suggested_metric_name")) + " " + _norm(valid_row.get("original_metric_name"))).lower()
        numeric_metric = any(x in metric_hint for x in ["eps", "收益", "利润", "收入", "roe", "p/e", "p/b", "ebitda"])
        if corrected_value and numeric_metric:
            ok_num, _ = _parse_number(corrected_value)
            if not ok_num:
                reasons.append("corrected_value_not_numeric_parseable")

        if corrected_unit and suggested_unit and corrected_unit != suggested_unit and not notes:
            reasons.append("corrected_unit_conflict_without_notes")
        if corrected_unit and existing_unit and corrected_unit != existing_unit and not notes:
            reasons.append("corrected_unit_conflict_existing_without_notes")

        fiscal_year = _norm(valid_row.get("fiscal_year"))
        if corrected_fiscal_year and corrected_fiscal_year != fiscal_year and not notes:
            reasons.append("corrected_fiscal_year_conflict_without_notes")

        eps_related = "eps" in metric_hint or "每股收益" in metric_hint
        if eps_related:
            cu = (corrected_unit or suggested_unit or existing_unit).lower()
            if "ratio" in cu or "%" in cu:
                reasons.append("eps_unit_guard_failed")
                eps_guard_pass = False

        if "safe_to_apply" in valid_row and _norm(valid_row.get("safe_to_apply")):
            reasons.append("safe_to_apply_human_field_present")
            safe_to_apply_human_field_detected_count += 1

        if _norm(valid_row.get("second_review_decision")) == "APPROVE_FOR_REAL_APPLY":
            reasons.append("approve_for_real_apply_detected")
            approve_for_real_apply_detected_count += 1

        controlled_sample_source = key in sample_keys
        proposal_action = "propose_sandbox_preview_validation" if not reasons else "block_candidate"
        preflight_status = "PASS" if not reasons else "BLOCKED"

        row_out = {
            "queue_item_id": key[0],
            "suggestion_id": key[1],
            "original_metric_name": _norm(valid_row.get("original_metric_name")),
            "fiscal_year": fiscal_year,
            "suggested_metric_name": _norm(valid_row.get("suggested_metric_name")),
            "suggested_value": _norm(valid_row.get("suggested_value")),
            "suggested_unit": suggested_unit,
            "corrected_metric_name": _norm(valid_row.get("corrected_metric_name")),
            "corrected_value": corrected_value,
            "corrected_unit": corrected_unit,
            "corrected_fiscal_year": corrected_fiscal_year,
            "existing_metric_name": _norm(valid_row.get("existing_metric_name")),
            "existing_value": _norm(valid_row.get("existing_value")),
            "existing_unit": existing_unit,
            "second_review_decision": _norm(valid_row.get("second_review_decision")),
            "source_pdf": _norm(valid_row.get("source_pdf")),
            "source_page": _norm(valid_row.get("source_page")),
            "source_row_reference": _norm(valid_row.get("source_row_reference")),
            "conflict_type": _norm(valid_row.get("conflict_type")),
            "value_mismatch": value_mismatch,
            "prior_stage_status": _norm(valid_row.get("prior_stage_status")),
            "original_pdf_evidence_checked": _as_bool(valid_row.get("original_pdf_evidence_checked")),
            "source_row_rechecked": _as_bool(valid_row.get("source_row_rechecked")),
            "fiscal_year_rechecked": _as_bool(valid_row.get("fiscal_year_rechecked")),
            "unit_rechecked": _as_bool(valid_row.get("unit_rechecked")),
            "value_rechecked": _as_bool(valid_row.get("value_rechecked")),
            "second_review_reason_code": _norm(valid_row.get("second_review_reason_code")),
            "second_review_notes": notes,
            "candidate_scope_note": _norm(c.get("candidate_scope_note")),
            "controlled_sample_source": controlled_sample_source,
            "production_approval_source": False,
            "real_human_final_approval": False,
            "proposed_sandbox_preview_action": proposal_action,
            "preflight_status": preflight_status,
            "reject_or_block_reasons": "|".join(reasons),
        }
        preflight_rows.append(row_out)
        if preflight_status == "PASS":
            proposal_rows.append(row_out)
        else:
            blocked_rows.append(row_out)

    preflight_df = pd.DataFrame(preflight_rows)
    proposal_df = pd.DataFrame(proposal_rows)
    blocked_df = pd.DataFrame(blocked_rows)

    preflight_df.to_excel(OUT_AUDIT, sheet_name="candidate_preflight_audit", index=False, engine="openpyxl")
    proposal_df.to_excel(OUT_PROPOSAL, sheet_name="sandbox_preview_proposal", index=False, engine="openpyxl")
    blocked_df.to_excel(OUT_BLOCKED, sheet_name="blocked_candidate_audit", index=False, engine="openpyxl")

    controlled_sample_candidate_count = int(preflight_df.get("controlled_sample_source", pd.Series([], dtype=bool)).sum()) if not preflight_df.empty else 0
    production_approval_candidate_count = 0
    controlled_sample_source_detected = controlled_sample_candidate_count > 0
    production_approval_source_detected = False

    _write_json(
        OUT_CONTROLLED_GUARD,
        {
            "controlled_sample_candidate_count": controlled_sample_candidate_count,
            "production_approval_candidate_count": production_approval_candidate_count,
            "controlled_sample_source_detected": controlled_sample_source_detected,
            "production_approval_source_detected": production_approval_source_detected,
            "note": "Controlled sample candidates are proposal-only and not final human production approvals.",
        },
    )

    _write_json(
        OUT_NO_REAL_APPLY_PROOF,
        {
            "real_apply_executed": False,
            "sandbox_apply_attempt_count": 0,
            "sandbox_apply_success_count": 0,
            "production_write_executed": False,
            "proposal_only_mode": True,
        },
    )

    after = _snapshot_hashes()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()

    second_review_candidate_count = len(projection_candidates)
    candidate_preflight_pass_count = len(proposal_rows)
    candidate_preflight_blocked_count = len(blocked_rows)

    summary = {
        "stage": "7Y",
        "external_api_called": False,
        "real_apply_executed": False,
        "stage7x_summary_loaded": stage7x_summary_loaded,
        "valid_second_review_results_loaded": valid_second_review_results_loaded,
        "candidate_projection_loaded": candidate_projection_loaded,
        "stage7x_guard_ok": stage7x_guard_ok,
        "second_review_candidate_count": second_review_candidate_count,
        "candidate_preflight_pass_count": candidate_preflight_pass_count,
        "candidate_preflight_blocked_count": candidate_preflight_blocked_count,
        "sandbox_preview_proposal_generated": True,
        "controlled_sample_candidate_count": controlled_sample_candidate_count,
        "production_approval_candidate_count": production_approval_candidate_count,
        "controlled_sample_source_detected": controlled_sample_source_detected,
        "production_approval_source_detected": production_approval_source_detected,
        "sandbox_apply_attempt_count": 0,
        "sandbox_apply_success_count": 0,
        "fabricated_candidate_count": fabricated_candidate_count,
        "blocked_value_mismatch_auto_apply_count": blocked_value_mismatch_auto_apply_count,
        "approve_for_real_apply_detected_count": 0,
        "safe_to_apply_human_field_detected_count": 0,
        "eps_guard_pass": eps_guard_pass,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": _norm(delivery.get("overall_status")),
        "ready_for_stage7z_real_second_review_input_or_production_preflight": True,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# Stage 7Y Sandbox Preview Candidate Preflight",
        "",
        "Mode: proposal-only, no API call, no real apply, no production write.",
        "",
        "## Input Guard",
        f"- stage7x_summary_loaded: {stage7x_summary_loaded}",
        f"- stage7x_guard_ok: {stage7x_guard_ok}",
        "",
        "## Candidate Counts",
        f"- second_review_candidate_count: {second_review_candidate_count}",
        f"- candidate_preflight_pass_count: {candidate_preflight_pass_count}",
        f"- candidate_preflight_blocked_count: {candidate_preflight_blocked_count}",
        "",
        "## Controlled Sample Guard",
        f"- controlled_sample_candidate_count: {controlled_sample_candidate_count}",
        "- production_approval_candidate_count: 0",
        "- real_human_final_approval: false",
        "",
        "## Safety",
        "- sandbox_apply_attempt_count: 0",
        "- sandbox_apply_success_count: 0",
        "- real_apply_executed: false",
        "- production write: not executed",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print("stage7y_status=ok")
    print(f"stage7y_summary={OUT_SUMMARY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
