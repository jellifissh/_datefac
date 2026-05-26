import copy
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

BASE_DIR = Path(r"D:\_datefac")

IN_8A_DIR = BASE_DIR / "output" / "stage8a_real_second_review_input_intake_gate"
IN_8A_SUMMARY = IN_8A_DIR / "214_stage8a_real_second_review_intake_summary.json"
IN_8A_MANIFEST = IN_8A_DIR / "214_stage8a_real_second_review_intake_manifest.json"
IN_8A_SHALLOW = IN_8A_DIR / "214_stage8a_real_input_shallow_check.json"
IN_8A_NO_APPLY = IN_8A_DIR / "214_stage8a_no_apply_proof.json"

IN_7W_DIR = BASE_DIR / "output" / "stage7w_second_review_needs_more_info_package"
IN_7W_SUMMARY = IN_7W_DIR / "210_stage7w_second_review_summary.json"
IN_7W_QUEUE = IN_7W_DIR / "210_stage7w_second_review_queue.xlsx"
IN_7W_TEMPLATE = IN_7W_DIR / "210_stage7w_second_review_input_template.xlsx"
IN_7W_POLICY = IN_7W_DIR / "210_stage7w_second_review_validation_policy.json"
IN_7W_NEXT = IN_7W_DIR / "210_stage7w_next_action_audit.xlsx"
IN_7W_NEEDS = IN_7W_DIR / "210_stage7w_needs_more_info_questions.xlsx"

REAL_INPUT = BASE_DIR / "input" / "real_second_review" / "stage8a_real_second_review_input.xlsx"

OUT_DIR = BASE_DIR / "output" / "stage8b_real_second_review_input_validation"
OUT_SUMMARY = OUT_DIR / "215_stage8b_real_second_review_validation_summary.json"
OUT_REPORT = OUT_DIR / "215_stage8b_real_second_review_validation_report.md"
OUT_VALID = OUT_DIR / "215_stage8b_valid_real_second_review_results.xlsx"
OUT_INVALID = OUT_DIR / "215_stage8b_invalid_real_second_review_results.xlsx"
OUT_PROJECTION = OUT_DIR / "215_stage8b_real_second_review_candidate_projection.xlsx"
OUT_AUDIT = OUT_DIR / "215_stage8b_validation_audit.xlsx"
OUT_NEG = OUT_DIR / "215_stage8b_negative_validation_tests.json"
OUT_NO_APPLY = OUT_DIR / "215_stage8b_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

EXPECTED_SCHEMA_VERSION = "stage7w_second_review_input_v1"
ALLOWED_DECISIONS = {
    "CONFIRM_NEEDS_MORE_INFO",
    "CONFIRM_REJECT",
    "APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE",
    "ESCALATE_TO_MANUAL_ACCOUNTING_REVIEW",
}
FORBIDDEN_DECISIONS = {"APPROVE_FOR_REAL_APPLY", "SAFE_TO_APPLY"}
FORBIDDEN_FIELDS = {
    "safe_to_apply",
    "approve_for_real_apply",
    "real_apply",
    "write_production",
    "production_apply",
}
IMMUTABLE_FIELDS = [
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
]


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


def _parse_dt_ok(v: Any) -> bool:
    text = _norm(v)
    if not text:
        return False
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
        return True
    except Exception:
        return False


def _parse_number(text: Any) -> bool:
    s = _norm(text).replace(",", "")
    if not s:
        return False
    return re.fullmatch(r"[-+]?\d+(\.\d+)?", s) is not None


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


def _validate_row(
    row: Dict[str, Any],
    queue_map: Dict[Tuple[str, str], Dict[str, Any]],
    seen_key: set,
    seen_queue_only: set,
    seen_suggestion_only: set,
) -> Tuple[List[str], bool]:
    errors: List[str] = []
    qid = _norm(row.get("queue_item_id"))
    sid = _norm(row.get("suggestion_id"))
    key = (qid, sid)

    if not qid:
        errors.append("queue_item_id_missing")
    if not sid:
        errors.append("suggestion_id_missing")

    if key in seen_key:
        errors.append("duplicate_queue_item_id_and_suggestion_id")
    else:
        seen_key.add(key)

    if qid in seen_queue_only:
        errors.append("duplicate_queue_item_id")
    else:
        seen_queue_only.add(qid)

    if sid in seen_suggestion_only:
        errors.append("duplicate_suggestion_id")
    else:
        seen_suggestion_only.add(sid)

    schema_version = _norm(row.get("schema_version"))
    reviewer_id = _norm(row.get("second_reviewer_id"))
    reviewer_role = _norm(row.get("second_reviewer_role"))
    decision = _norm(row.get("second_review_decision"))
    reason_code = _norm(row.get("second_review_reason_code"))
    notes = _norm(row.get("second_review_notes"))
    reviewed_at = _norm(row.get("reviewed_at_utc"))

    if schema_version != EXPECTED_SCHEMA_VERSION:
        errors.append("schema_version_invalid")
    if not reviewer_id:
        errors.append("second_reviewer_id_missing")
    if not reviewer_role:
        errors.append("second_reviewer_role_missing")
    if not decision:
        errors.append("second_review_decision_missing")
    if decision not in ALLOWED_DECISIONS:
        errors.append("invalid_second_review_decision_enum")
    if decision in FORBIDDEN_DECISIONS:
        errors.append("forbidden_second_review_decision")
    if not reason_code:
        errors.append("second_review_reason_code_missing")
    if not notes:
        errors.append("second_review_notes_missing")
    if not _parse_dt_ok(reviewed_at):
        errors.append("reviewed_at_utc_invalid")

    # Forbidden fields (if present and non-empty)
    for f in FORBIDDEN_FIELDS:
        if f in row and _norm(row.get(f)):
            errors.append(f"forbidden_field_present:{f}")

    queue_row = queue_map.get(key)
    if queue_row is None:
        errors.append("queue_row_not_found")
    else:
        for f in IMMUTABLE_FIELDS:
            if _norm(row.get(f)) != _norm(queue_row.get(f)):
                errors.append(f"immutable_field_changed:{f}")

    value_mismatch = _as_bool(row.get("value_mismatch"))
    conflict_type = _norm(row.get("conflict_type")).lower()
    prior_stage_status = _norm(row.get("prior_stage_status")).lower()
    corrected_value = _norm(row.get("corrected_value"))
    corrected_unit = _norm(row.get("corrected_unit"))
    corrected_fiscal_year = _norm(row.get("corrected_fiscal_year"))

    source_row_rechecked = _as_bool(row.get("source_row_rechecked"))
    fiscal_year_rechecked = _as_bool(row.get("fiscal_year_rechecked"))
    unit_rechecked = _as_bool(row.get("unit_rechecked"))
    value_rechecked = _as_bool(row.get("value_rechecked"))
    original_pdf_evidence_checked = _as_bool(row.get("original_pdf_evidence_checked"))

    is_candidate = False
    if decision == "CONFIRM_NEEDS_MORE_INFO":
        if not _norm(row.get("remaining_question")):
            errors.append("needs_more_info_remaining_question_missing")
    elif decision == "CONFIRM_REJECT":
        pass
    elif decision == "ESCALATE_TO_MANUAL_ACCOUNTING_REVIEW":
        pass
    elif decision == "APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE":
        for flag_name, flag_val in [
            ("source_row_rechecked", source_row_rechecked),
            ("fiscal_year_rechecked", fiscal_year_rechecked),
            ("unit_rechecked", unit_rechecked),
            ("value_rechecked", value_rechecked),
            ("original_pdf_evidence_checked", original_pdf_evidence_checked),
        ]:
            if not flag_val:
                errors.append(f"candidate_missing_required_flag:{flag_name}")

        if value_mismatch and not corrected_value:
            errors.append("value_mismatch_without_corrected_value")
        if corrected_unit and not unit_rechecked:
            errors.append("corrected_unit_without_unit_rechecked")
        if corrected_fiscal_year and not fiscal_year_rechecked:
            errors.append("corrected_fiscal_year_without_fiscal_year_rechecked")

        if "true_value_conflict" in conflict_type and not corrected_value:
            errors.append("true_value_conflict_requires_corrected_value_or_escalate")
        if "blocked_apply_value_mismatch" in prior_stage_status and not corrected_value:
            errors.append("blocked_apply_value_mismatch_requires_corrected_value")

        metric_hint = (
            _norm(row.get("suggested_metric_name")) + " " + _norm(row.get("original_metric_name"))
        ).lower()
        numeric_metric = any(k in metric_hint for k in ["eps", "收益", "利润", "收入", "roe", "p/e", "p/b", "ebitda"])
        if corrected_value and numeric_metric and not _parse_number(corrected_value):
            errors.append("corrected_value_not_numeric")

        is_candidate = len(errors) == 0

    row_valid = len(errors) == 0
    return errors, (is_candidate and row_valid)


def _run_negative_tests(base_row: Dict[str, Any], queue_map: Dict[Tuple[str, str], Dict[str, Any]]) -> Dict[str, Any]:
    tests: List[Dict[str, Any]] = []

    def run_case(name: str, rows: List[Dict[str, Any]], expect_error_prefix: str) -> Dict[str, Any]:
        seen_key, seen_q, seen_s = set(), set(), set()
        all_err: List[List[str]] = []
        for r in rows:
            err, _ = _validate_row(r, queue_map, seen_key, seen_q, seen_s)
            all_err.append(err)
        flat = [x for arr in all_err for x in arr]
        hit = any(e == expect_error_prefix or e.startswith(expect_error_prefix) for e in flat)
        return {"name": name, "expected_error": expect_error_prefix, "detected": hit, "errors": all_err}

    r1 = copy.deepcopy(base_row)
    r1["second_reviewer_id"] = ""
    tests.append(run_case("missing_second_reviewer_id", [r1], "second_reviewer_id_missing"))

    r2 = copy.deepcopy(base_row)
    r2["second_review_decision"] = "INVALID_DECISION"
    tests.append(run_case("invalid_second_review_decision", [r2], "invalid_second_review_decision_enum"))

    r3 = copy.deepcopy(base_row)
    r3["second_review_decision"] = "APPROVE_FOR_REAL_APPLY"
    tests.append(run_case("approve_for_real_apply", [r3], "invalid_second_review_decision_enum"))

    r4 = copy.deepcopy(base_row)
    r4["safe_to_apply"] = "true"
    tests.append(run_case("safe_to_apply_human_field", [r4], "forbidden_field_present:safe_to_apply"))

    r5 = copy.deepcopy(base_row)
    r5["source_pdf"] = "tampered.pdf"
    tests.append(run_case("immutable_field_tampering", [r5], "immutable_field_changed:source_pdf"))

    r6 = copy.deepcopy(base_row)
    r6["second_review_decision"] = "APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE"
    r6["source_row_rechecked"] = False
    r6["fiscal_year_rechecked"] = False
    r6["unit_rechecked"] = False
    r6["value_rechecked"] = False
    r6["original_pdf_evidence_checked"] = False
    tests.append(run_case("candidate_without_evidence_checks", [r6], "candidate_missing_required_flag:source_row_rechecked"))

    r7 = copy.deepcopy(base_row)
    r7["second_review_decision"] = "APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE"
    r7["value_mismatch"] = True
    r7["source_row_rechecked"] = True
    r7["fiscal_year_rechecked"] = True
    r7["unit_rechecked"] = True
    r7["value_rechecked"] = True
    r7["original_pdf_evidence_checked"] = True
    r7["corrected_value"] = ""
    tests.append(run_case("value_mismatch_candidate_without_corrected_value", [r7], "value_mismatch_without_corrected_value"))

    r8a = copy.deepcopy(base_row)
    r8b = copy.deepcopy(base_row)
    tests.append(run_case("duplicate_queue_suggestion", [r8a, r8b], "duplicate_queue_item_id_and_suggestion_id"))

    r9 = copy.deepcopy(base_row)
    r9["reviewed_at_utc"] = "not-a-datetime"
    tests.append(run_case("malformed_reviewed_at_utc", [r9], "reviewed_at_utc_invalid"))

    return {"tests": tests}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [
        IN_8A_SUMMARY,
        IN_8A_MANIFEST,
        IN_8A_SHALLOW,
        IN_8A_NO_APPLY,
        IN_7W_SUMMARY,
        IN_7W_QUEUE,
        IN_7W_TEMPLATE,
        IN_7W_POLICY,
        IN_7W_NEXT,
        IN_7W_NEEDS,
        REAL_INPUT,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "8B",
                "external_api_called": False,
                "real_apply_executed": False,
                "stage8a_summary_loaded": False,
                "blocked": True,
                "blocked_reason": f"missing_input:{'|'.join(missing)}",
            },
        )
        print("stage8b_status=blocked_missing_input")
        return 0

    before = _snapshot_hashes()

    s8a = _load_json(IN_8A_SUMMARY)
    _ = _load_json(IN_8A_MANIFEST)
    shallow = _load_json(IN_8A_SHALLOW)
    _ = _load_json(IN_8A_NO_APPLY)

    _ = _load_json(IN_7W_SUMMARY)
    queue_df = pd.read_excel(IN_7W_QUEUE)
    _ = pd.read_excel(IN_7W_TEMPLATE)
    _ = _load_json(IN_7W_POLICY)
    _ = pd.read_excel(IN_7W_NEXT)
    _ = pd.read_excel(IN_7W_NEEDS)

    real_df = pd.read_excel(REAL_INPUT)

    stage8a_summary_loaded = True
    stage8a_gate_verified = bool(
        s8a.get("real_second_review_input_present") is True
        and s8a.get("real_second_review_input_readable") is True
        and s8a.get("shallow_schema_check_pass") is True
        and _norm(s8a.get("intake_status")) == "READY_FOR_STAGE8B_SHALLOW_CHECK_PASS"
        and s8a.get("ready_for_stage8b_real_second_review_validation") is True
        and s8a.get("ready_for_production_preflight") is False
        and _norm(s8a.get("check_delivery_state_overall_status")) == "PASS"
        and shallow.get("real_second_review_input_present") is True
        and shallow.get("real_second_review_input_readable") is True
        and shallow.get("shallow_schema_check_pass") is True
    )

    stage7w_queue_loaded = True
    real_second_review_input_loaded = True

    # Fast schema-level checks
    forbidden_columns_present = [c for c in real_df.columns if c.lower() in FORBIDDEN_FIELDS]
    real_second_review_input_schema_valid = (
        "schema_version" in real_df.columns
        and len(real_df) > 0
        and all(_norm(v) == EXPECTED_SCHEMA_VERSION for v in real_df["schema_version"].tolist())
        and len(forbidden_columns_present) == 0
    )

    queue_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for _, r in queue_df.iterrows():
        d = r.to_dict()
        queue_map[(_norm(d.get("queue_item_id")), _norm(d.get("suggestion_id")))] = d

    seen_key, seen_q, seen_s = set(), set(), set()
    valid_rows: List[Dict[str, Any]] = []
    invalid_rows: List[Dict[str, Any]] = []
    audit_rows: List[Dict[str, Any]] = []
    projection_rows: List[Dict[str, Any]] = []

    blocked_value_mismatch_auto_apply_count = 0

    for _, r in real_df.iterrows():
        row = r.to_dict()
        errs, candidate = _validate_row(row, queue_map, seen_key, seen_q, seen_s)
        row_valid = len(errs) == 0
        value_mismatch = _as_bool(row.get("value_mismatch"))
        if candidate and value_mismatch:
            blocked_value_mismatch_auto_apply_count += 1
        decision = _norm(row.get("second_review_decision"))

        out = dict(row)
        out["row_valid"] = row_valid
        out["validation_errors"] = "|".join(errs)
        out["sandbox_preview_candidate"] = bool(candidate)

        if row_valid:
            valid_rows.append(out)
        else:
            invalid_rows.append(out)

        audit_rows.append(
            {
                "queue_item_id": _norm(row.get("queue_item_id")),
                "suggestion_id": _norm(row.get("suggestion_id")),
                "second_review_decision": decision,
                "row_valid": row_valid,
                "sandbox_preview_candidate": bool(candidate),
                "validation_errors": "|".join(errs),
            }
        )

        projection_rows.append(
            {
                "queue_item_id": _norm(row.get("queue_item_id")),
                "suggestion_id": _norm(row.get("suggestion_id")),
                "second_review_decision": decision,
                "row_valid": row_valid,
                "value_mismatch": value_mismatch,
                "conflict_type": _norm(row.get("conflict_type")),
                "prior_stage_status": _norm(row.get("prior_stage_status")),
                "sandbox_preview_candidate": bool(candidate),
                "candidate_scope_note": "future_sandbox_preview_validation_only" if candidate else "",
            }
        )

    valid_df = pd.DataFrame(valid_rows)
    invalid_df = pd.DataFrame(invalid_rows)
    audit_df = pd.DataFrame(audit_rows)
    proj_df = pd.DataFrame(projection_rows)

    valid_df.to_excel(OUT_VALID, sheet_name="valid_real_second_review", index=False, engine="openpyxl")
    invalid_df.to_excel(OUT_INVALID, sheet_name="invalid_real_second_review", index=False, engine="openpyxl")
    audit_df.to_excel(OUT_AUDIT, sheet_name="validation_audit", index=False, engine="openpyxl")
    proj_df.to_excel(OUT_PROJECTION, sheet_name="real_candidate_projection", index=False, engine="openpyxl")

    # Negative tests with synthetic rows only
    base_row = valid_rows[0] if valid_rows else real_df.iloc[0].to_dict()
    neg = _run_negative_tests(base_row, queue_map)
    _write_json(OUT_NEG, neg)

    def _detected(name: str) -> bool:
        for t in neg.get("tests", []):
            if t.get("name") == name:
                return bool(t.get("detected"))
        return False

    real_second_review_input_row_count = len(real_df)
    valid_real_second_review_count = len(valid_df)
    invalid_real_second_review_count = len(invalid_df)
    confirm_needs_more_info_count = int((valid_df.get("second_review_decision", pd.Series([], dtype=str)) == "CONFIRM_NEEDS_MORE_INFO").sum())
    confirm_reject_count = int((valid_df.get("second_review_decision", pd.Series([], dtype=str)) == "CONFIRM_REJECT").sum())
    escalate_manual_accounting_review_count = int(
        (valid_df.get("second_review_decision", pd.Series([], dtype=str)) == "ESCALATE_TO_MANUAL_ACCOUNTING_REVIEW").sum()
    )
    approve_for_sandbox_preview_candidate_count = int(
        (valid_df.get("second_review_decision", pd.Series([], dtype=str)) == "APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE").sum()
    )
    real_sandbox_preview_candidate_count = int(proj_df.get("sandbox_preview_candidate", pd.Series([], dtype=bool)).sum())

    _write_json(
        OUT_NO_APPLY,
        {
            "external_api_called": False,
            "real_apply_executed": False,
            "sandbox_apply_attempt_count": 0,
            "sandbox_apply_success_count": 0,
            "production_apply_attempt_count": 0,
            "production_apply_success_count": 0,
            "note": "Stage 8B validation only; no apply actions.",
        },
    )

    after = _snapshot_hashes()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    delivery_pass = _norm(delivery.get("overall_status")) == "PASS"

    ready_for_stage8c_real_sandbox_preview_candidate_preflight = bool(
        real_second_review_input_schema_valid and invalid_real_second_review_count == 0 and delivery_pass
    )

    summary = {
        "stage": "8B",
        "external_api_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "sandbox_apply_success_count": 0,
        "production_apply_attempt_count": 0,
        "stage8a_summary_loaded": stage8a_summary_loaded,
        "stage8a_gate_verified": stage8a_gate_verified,
        "stage7w_queue_loaded": stage7w_queue_loaded,
        "real_second_review_input_loaded": real_second_review_input_loaded,
        "real_second_review_input_schema_valid": real_second_review_input_schema_valid,
        "real_second_review_input_row_count": real_second_review_input_row_count,
        "valid_real_second_review_count": valid_real_second_review_count,
        "invalid_real_second_review_count": invalid_real_second_review_count,
        "confirm_needs_more_info_count": confirm_needs_more_info_count,
        "confirm_reject_count": confirm_reject_count,
        "escalate_manual_accounting_review_count": escalate_manual_accounting_review_count,
        "approve_for_sandbox_preview_candidate_count": approve_for_sandbox_preview_candidate_count,
        "real_sandbox_preview_candidate_count": real_sandbox_preview_candidate_count,
        "candidate_projection_generated": True,
        "approve_for_real_apply_rejected": _detected("approve_for_real_apply"),
        "safe_to_apply_human_field_rejected": _detected("safe_to_apply_human_field"),
        "immutable_field_tamper_detected": _detected("immutable_field_tampering"),
        "missing_second_reviewer_id_detected": _detected("missing_second_reviewer_id"),
        "invalid_decision_enum_detected": _detected("invalid_second_review_decision"),
        "value_mismatch_without_corrected_value_rejected": _detected("value_mismatch_candidate_without_corrected_value"),
        "evidence_checks_required_for_candidate": _detected("candidate_without_evidence_checks"),
        "duplicate_second_review_detected": _detected("duplicate_queue_suggestion"),
        "malformed_reviewed_at_detected": _detected("malformed_reviewed_at_utc"),
        "blocked_value_mismatch_auto_apply_count": blocked_value_mismatch_auto_apply_count,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": _norm(delivery.get("overall_status")),
        "ready_for_stage8c_real_sandbox_preview_candidate_preflight": ready_for_stage8c_real_sandbox_preview_candidate_preflight,
        "ready_for_production_preflight": False,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# Stage 8B Real Second-Review Input Deep Validation",
        "",
        "Mode: no API call, no sandbox apply, no real apply, no production write.",
        "",
        "## Gate Check",
        f"- stage8a_gate_verified: {stage8a_gate_verified}",
        f"- real_second_review_input_schema_valid: {real_second_review_input_schema_valid}",
        "",
        "## Validation Counts",
        f"- real_second_review_input_row_count: {real_second_review_input_row_count}",
        f"- valid_real_second_review_count: {valid_real_second_review_count}",
        f"- invalid_real_second_review_count: {invalid_real_second_review_count}",
        f"- confirm_needs_more_info_count: {confirm_needs_more_info_count}",
        f"- confirm_reject_count: {confirm_reject_count}",
        f"- escalate_manual_accounting_review_count: {escalate_manual_accounting_review_count}",
        f"- approve_for_sandbox_preview_candidate_count: {approve_for_sandbox_preview_candidate_count}",
        f"- real_sandbox_preview_candidate_count: {real_sandbox_preview_candidate_count}",
        "",
        "## Safety",
        "- Candidate output is for future sandbox preview validation only.",
        "- No apply attempted, no production write executed.",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print("stage8b_status=ok")
    print(f"stage8b_summary={OUT_SUMMARY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
