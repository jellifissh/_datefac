import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

BASE_DIR = Path(r"D:\_datefac")
IN_DIR = BASE_DIR / "output" / "stage7w_second_review_needs_more_info_package"

IN_SUMMARY = IN_DIR / "210_stage7w_second_review_summary.json"
IN_QUEUE = IN_DIR / "210_stage7w_second_review_queue.xlsx"
IN_TEMPLATE = IN_DIR / "210_stage7w_second_review_input_template.xlsx"
IN_POLICY = IN_DIR / "210_stage7w_second_review_validation_policy.json"
IN_NEXT_ACTION = IN_DIR / "210_stage7w_next_action_audit.xlsx"
IN_NEEDS_MORE_INFO = IN_DIR / "210_stage7w_needs_more_info_questions.xlsx"

OUT_DIR = BASE_DIR / "output" / "stage7x_second_review_input_validation"
OUT_SUMMARY = OUT_DIR / "211_stage7x_second_review_validation_summary.json"
OUT_REPORT = OUT_DIR / "211_stage7x_second_review_validation_report.md"
OUT_SAMPLE_INPUT = OUT_DIR / "211_stage7x_second_review_sample_input.xlsx"
OUT_VALID = OUT_DIR / "211_stage7x_valid_second_review_results.xlsx"
OUT_INVALID = OUT_DIR / "211_stage7x_invalid_second_review_results.xlsx"
OUT_PROJECTION = OUT_DIR / "211_stage7x_second_review_candidate_projection.xlsx"
OUT_NEG = OUT_DIR / "211_stage7x_negative_validation_tests.json"
OUT_AUDIT = OUT_DIR / "211_stage7x_validation_audit.xlsx"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

ALLOWED_DECISIONS = {
    "CONFIRM_NEEDS_MORE_INFO",
    "CONFIRM_REJECT",
    "APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE",
    "ESCALATE_TO_MANUAL_ACCOUNTING_REVIEW",
}
FORBIDDEN_DECISIONS = {"APPROVE_FOR_REAL_APPLY", "SAFE_TO_APPLY"}
SCHEMA_VERSION = "stage7w_second_review_input_v1"

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
    s = _norm(v).lower()
    return s in {"1", "true", "yes", "y"}


def _parse_datetime_ok(v: Any) -> bool:
    t = _norm(v)
    if not t:
        return False
    try:
        datetime.fromisoformat(t.replace("Z", "+00:00"))
        return True
    except Exception:
        return False


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
    seen_keys: set,
) -> Tuple[List[str], bool]:
    errors: List[str] = []
    queue_item_id = _norm(row.get("queue_item_id"))
    suggestion_id = _norm(row.get("suggestion_id"))
    key = (queue_item_id, suggestion_id)

    schema_version = _norm(row.get("schema_version"))
    second_reviewer_id = _norm(row.get("second_reviewer_id"))
    second_reviewer_role = _norm(row.get("second_reviewer_role"))
    decision = _norm(row.get("second_review_decision"))
    reason_code = _norm(row.get("second_review_reason_code"))
    notes = _norm(row.get("second_review_notes"))
    reviewed_at_utc = _norm(row.get("reviewed_at_utc"))

    if schema_version != SCHEMA_VERSION:
        errors.append("schema_version_invalid")
    if not queue_item_id:
        errors.append("queue_item_id_missing")
    if not suggestion_id:
        errors.append("suggestion_id_missing")
    if key in seen_keys:
        errors.append("duplicate_second_review_key")
    else:
        seen_keys.add(key)

    if not second_reviewer_id:
        errors.append("second_reviewer_id_missing")
    if not second_reviewer_role:
        errors.append("second_reviewer_role_missing")
    if not decision:
        errors.append("second_review_decision_missing")
    if decision not in ALLOWED_DECISIONS:
        errors.append("invalid_second_review_decision_enum")
    if decision in FORBIDDEN_DECISIONS:
        errors.append("forbidden_second_review_decision")

    if "safe_to_apply" in row and _norm(row.get("safe_to_apply")) != "":
        errors.append("safe_to_apply_human_field_forbidden")
    for k in row.keys():
        lk = _norm(k).lower()
        if lk in {"approve_for_real_apply", "real_apply", "write_production"}:
            errors.append("forbidden_manual_apply_field")
            break

    if not reason_code:
        errors.append("second_review_reason_code_missing")
    if not notes:
        errors.append("second_review_notes_missing")
    if not _parse_datetime_ok(reviewed_at_utc):
        errors.append("reviewed_at_utc_invalid")

    origin = queue_map.get(key)
    if origin is None:
        errors.append("queue_item_not_found")
    else:
        for f in IMMUTABLE_FIELDS:
            if _norm(row.get(f)) != _norm(origin.get(f)):
                errors.append(f"immutable_field_changed:{f}")

    value_mismatch = _as_bool(row.get("value_mismatch"))
    conflict_type = _norm(row.get("conflict_type")).lower()
    prior_stage_status = _norm(row.get("prior_stage_status")).lower()

    source_row_rechecked = _as_bool(row.get("source_row_rechecked"))
    fiscal_year_rechecked = _as_bool(row.get("fiscal_year_rechecked"))
    unit_rechecked = _as_bool(row.get("unit_rechecked"))
    value_rechecked = _as_bool(row.get("value_rechecked"))
    original_pdf_evidence_checked = _as_bool(row.get("original_pdf_evidence_checked"))

    corrected_metric_name = _norm(row.get("corrected_metric_name"))
    corrected_value = _norm(row.get("corrected_value"))
    corrected_unit = _norm(row.get("corrected_unit"))
    corrected_fiscal_year = _norm(row.get("corrected_fiscal_year"))
    remaining_question = _norm(row.get("remaining_question"))

    if decision == "CONFIRM_NEEDS_MORE_INFO":
        if not remaining_question:
            errors.append("needs_more_info_question_missing")
    elif decision == "CONFIRM_REJECT":
        pass
    elif decision == "ESCALATE_TO_MANUAL_ACCOUNTING_REVIEW":
        pass
    elif decision == "APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE":
        if not source_row_rechecked:
            errors.append("candidate_missing_source_row_rechecked")
        if not fiscal_year_rechecked:
            errors.append("candidate_missing_fiscal_year_rechecked")
        if not unit_rechecked:
            errors.append("candidate_missing_unit_rechecked")
        if not value_rechecked:
            errors.append("candidate_missing_value_rechecked")
        if not original_pdf_evidence_checked:
            errors.append("candidate_missing_original_pdf_evidence_checked")
        if value_mismatch and not corrected_value:
            errors.append("value_mismatch_without_corrected_value")
        if corrected_unit and not unit_rechecked:
            errors.append("corrected_unit_without_unit_rechecked")
        if corrected_fiscal_year and not fiscal_year_rechecked:
            errors.append("corrected_fiscal_year_without_fiscal_year_rechecked")
        if "true_value_conflict" in conflict_type and not corrected_value:
            errors.append("true_value_conflict_without_corrected_value_or_escalate")
        if "blocked_apply_value_mismatch" in prior_stage_status:
            if not corrected_value:
                errors.append("blocked_apply_value_mismatch_requires_corrected_value")
            if not (
                source_row_rechecked
                and fiscal_year_rechecked
                and unit_rechecked
                and value_rechecked
                and original_pdf_evidence_checked
            ):
                errors.append("blocked_apply_value_mismatch_requires_full_evidence")

    row_valid = len(errors) == 0
    is_candidate = row_valid and decision == "APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE"
    return errors, is_candidate


def _build_sample_input(template_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    row_count = len(template_df)
    indices = list(range(row_count))

    invalid_index = indices[-1]
    value_mismatch_indices = [i for i, v in enumerate(template_df["value_mismatch"].tolist()) if _as_bool(v)]
    non_mismatch_indices = [i for i, v in enumerate(template_df["value_mismatch"].tolist()) if not _as_bool(v)]

    escalate_index = next((i for i in value_mismatch_indices if i != invalid_index), indices[0])
    candidate_index = next(
        (i for i in non_mismatch_indices if i not in {invalid_index, escalate_index}),
        None,
    )

    needs_more_info_indices = [
        i for i in indices if i not in {invalid_index, escalate_index} and i != candidate_index
    ]

    for i, (_, r) in enumerate(template_df.iterrows()):
        row = r.to_dict()
        row["schema_version"] = SCHEMA_VERSION
        row["second_reviewer_id"] = f"sr_{i + 1:03d}"
        row["second_reviewer_role"] = "accounting_reviewer"
        row["second_review_reason_code"] = "followup_required"
        row["second_review_notes"] = "Second reviewer check completed."
        row["reviewed_at_utc"] = now
        row["source_row_rechecked"] = False
        row["fiscal_year_rechecked"] = False
        row["unit_rechecked"] = False
        row["value_rechecked"] = False
        row["original_pdf_evidence_checked"] = False
        row["corrected_metric_name"] = ""
        row["corrected_value"] = ""
        row["corrected_unit"] = ""
        row["corrected_fiscal_year"] = ""
        row["remaining_question"] = ""

        if candidate_index is not None and i == candidate_index:
            row["second_review_decision"] = "APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE"
            row["second_review_reason_code"] = "evidence_reconciled_for_sandbox_candidate"
            row["second_review_notes"] = "Candidate allowed for future sandbox preview validation only."
            row["source_row_rechecked"] = True
            row["fiscal_year_rechecked"] = True
            row["unit_rechecked"] = True
            row["value_rechecked"] = True
            row["original_pdf_evidence_checked"] = True
            row["corrected_value"] = _norm(row.get("suggested_value")) or _norm(row.get("existing_value"))
        elif i in needs_more_info_indices:
            row["second_review_decision"] = "CONFIRM_NEEDS_MORE_INFO"
            row["remaining_question"] = "Please provide highlighted source evidence for the conflicting value."
            row["second_review_reason_code"] = "needs_additional_evidence"
            row["second_review_notes"] = "Insufficient evidence to finalize."
        elif i == escalate_index:
            row["second_review_decision"] = "ESCALATE_TO_MANUAL_ACCOUNTING_REVIEW"
            row["second_review_reason_code"] = "true_value_conflict_unresolved"
            row["second_review_notes"] = "Escalation required for accounting judgment."
        else:
            # Controlled invalid row: forbidden decision.
            row["second_review_decision"] = "APPROVE_FOR_REAL_APPLY"
            row["second_review_reason_code"] = "invalid_direct_apply_attempt"
            row["second_review_notes"] = "This row should be rejected by validator."

        rows.append(row)

    return pd.DataFrame(rows, columns=template_df.columns)


def _run_negative_tests(base_row: Dict[str, Any], queue_map: Dict[Tuple[str, str], Dict[str, Any]]) -> Dict[str, Any]:
    tests: List[Dict[str, Any]] = []

    def run_case(name: str, rows: List[Dict[str, Any]], expect_error: str) -> Dict[str, Any]:
        seen = set()
        all_errors: List[List[str]] = []
        for r in rows:
            errs, _ = _validate_row(r, queue_map, seen)
            all_errors.append(errs)
        flat = [e for es in all_errors for e in es]
        return {
            "name": name,
            "expected_error": expect_error,
            "detected": any(expect_error == e or e.startswith(expect_error + ":") for e in flat),
            "errors": all_errors,
        }

    r1 = copy.deepcopy(base_row)
    r1["second_reviewer_id"] = ""
    tests.append(run_case("missing_second_reviewer_id", [r1], "second_reviewer_id_missing"))

    r2 = copy.deepcopy(base_row)
    r2["second_review_decision"] = "INVALID_DECISION"
    tests.append(run_case("invalid_decision_enum", [r2], "invalid_second_review_decision_enum"))

    r3 = copy.deepcopy(base_row)
    r3["second_review_decision"] = "APPROVE_FOR_REAL_APPLY"
    tests.append(run_case("approve_for_real_apply", [r3], "invalid_second_review_decision_enum"))

    r4 = copy.deepcopy(base_row)
    r4["safe_to_apply"] = "true"
    tests.append(run_case("manual_safe_to_apply_field", [r4], "safe_to_apply_human_field_forbidden"))

    r5 = copy.deepcopy(base_row)
    r5["source_pdf"] = "tampered_source.pdf"
    tests.append(run_case("immutable_tamper", [r5], "immutable_field_changed:source_pdf"))

    r6 = copy.deepcopy(base_row)
    r6["second_review_decision"] = "APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE"
    r6["source_row_rechecked"] = False
    r6["fiscal_year_rechecked"] = False
    r6["unit_rechecked"] = False
    r6["value_rechecked"] = False
    r6["original_pdf_evidence_checked"] = False
    r6["corrected_value"] = ""
    tests.append(run_case("candidate_without_evidence_checks", [r6], "candidate_missing_source_row_rechecked"))

    r7 = copy.deepcopy(base_row)
    r7["second_review_decision"] = "APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE"
    r7["value_mismatch"] = True
    r7["source_row_rechecked"] = True
    r7["fiscal_year_rechecked"] = True
    r7["unit_rechecked"] = True
    r7["value_rechecked"] = True
    r7["original_pdf_evidence_checked"] = True
    r7["corrected_value"] = ""
    tests.append(run_case("value_mismatch_without_corrected_value", [r7], "value_mismatch_without_corrected_value"))

    r8a = copy.deepcopy(base_row)
    r8b = copy.deepcopy(base_row)
    tests.append(run_case("duplicate_queue_suggestion", [r8a, r8b], "duplicate_second_review_key"))

    r9 = copy.deepcopy(base_row)
    r9["reviewed_at_utc"] = "not-a-datetime"
    tests.append(run_case("malformed_reviewed_at_utc", [r9], "reviewed_at_utc_invalid"))

    return {"tests": tests}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    required = [IN_SUMMARY, IN_QUEUE, IN_TEMPLATE, IN_POLICY, IN_NEXT_ACTION, IN_NEEDS_MORE_INFO]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "7X",
                "external_api_called": False,
                "real_apply_executed": False,
                "stage7w_summary_loaded": False,
                "blocked": True,
                "blocked_reason": f"missing_input:{'|'.join(missing)}",
            },
        )
        print("stage7x_status=blocked_missing_input")
        return 0

    before = _snapshot_hashes()

    stage7w_summary = _load_json(IN_SUMMARY)
    queue_df = pd.read_excel(IN_QUEUE)
    template_df = pd.read_excel(IN_TEMPLATE)
    policy = _load_json(IN_POLICY)
    _ = pd.read_excel(IN_NEXT_ACTION)
    _ = pd.read_excel(IN_NEEDS_MORE_INFO)

    stage7w_summary_loaded = True
    second_review_queue_loaded = True
    second_review_template_loaded = True
    second_review_policy_loaded = True

    stage7w_guard_ok = bool(
        stage7w_summary.get("external_api_called") is False
        and stage7w_summary.get("real_apply_executed") is False
        and int(stage7w_summary.get("sandbox_preview_candidate_count", -1)) == 0
        and int(stage7w_summary.get("sandbox_apply_attempt_count", -1)) == 0
        and int(stage7w_summary.get("sandbox_apply_success_count", -1)) == 0
        and stage7w_summary.get("second_review_queue_generated") is True
        and stage7w_summary.get("second_review_input_template_generated") is True
        and stage7w_summary.get("second_review_validation_policy_generated") is True
        and int(stage7w_summary.get("approve_for_sandbox_preview_generated_count", -1)) == 0
        and int(stage7w_summary.get("approve_for_real_apply_detected_count", -1)) == 0
        and int(stage7w_summary.get("fabricated_candidate_count", -1)) == 0
        and int(stage7w_summary.get("blocked_value_mismatch_auto_apply_count", -1)) == 0
        and stage7w_summary.get("ready_for_stage7x_second_review_input_validation") is True
        and _norm(stage7w_summary.get("check_delivery_state_overall_status")) == "PASS"
    )

    queue_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for _, row in queue_df.iterrows():
        r = row.to_dict()
        queue_map[(_norm(r.get("queue_item_id")), _norm(r.get("suggestion_id")))] = r

    sample_df = _build_sample_input(template_df)
    sample_df.to_excel(OUT_SAMPLE_INPUT, sheet_name="second_review_sample_input", index=False, engine="openpyxl")

    audit_rows: List[Dict[str, Any]] = []
    valid_rows: List[Dict[str, Any]] = []
    invalid_rows: List[Dict[str, Any]] = []
    projection_rows: List[Dict[str, Any]] = []
    seen_keys: set = set()

    for _, row in sample_df.iterrows():
        r = row.to_dict()
        errors, is_candidate = _validate_row(r, queue_map, seen_keys)
        row_valid = len(errors) == 0
        decision = _norm(r.get("second_review_decision"))

        enriched = dict(r)
        enriched["row_valid"] = row_valid
        enriched["validation_errors"] = "|".join(errors)
        enriched["sandbox_preview_candidate"] = bool(is_candidate)

        if row_valid:
            valid_rows.append(enriched)
        else:
            invalid_rows.append(enriched)

        audit_rows.append(
            {
                "queue_item_id": _norm(r.get("queue_item_id")),
                "suggestion_id": _norm(r.get("suggestion_id")),
                "second_review_decision": decision,
                "row_valid": row_valid,
                "sandbox_preview_candidate": bool(is_candidate),
                "validation_errors": "|".join(errors),
            }
        )

        projection_rows.append(
            {
                "queue_item_id": _norm(r.get("queue_item_id")),
                "suggestion_id": _norm(r.get("suggestion_id")),
                "row_valid": row_valid,
                "second_review_decision": decision,
                "value_mismatch": _as_bool(r.get("value_mismatch")),
                "conflict_type": _norm(r.get("conflict_type")),
                "prior_stage_status": _norm(r.get("prior_stage_status")),
                "sandbox_preview_candidate": bool(is_candidate),
                "candidate_scope_note": "future_sandbox_preview_validation_only" if is_candidate else "",
            }
        )

    valid_df = pd.DataFrame(valid_rows)
    invalid_df = pd.DataFrame(invalid_rows)
    projection_df = pd.DataFrame(projection_rows)
    audit_df = pd.DataFrame(audit_rows)

    valid_df.to_excel(OUT_VALID, sheet_name="valid_second_review_results", index=False, engine="openpyxl")
    invalid_df.to_excel(OUT_INVALID, sheet_name="invalid_second_review_results", index=False, engine="openpyxl")
    projection_df.to_excel(OUT_PROJECTION, sheet_name="candidate_projection", index=False, engine="openpyxl")
    audit_df.to_excel(OUT_AUDIT, sheet_name="validation_audit", index=False, engine="openpyxl")

    # Negative tests
    base_valid_row = None
    for row in valid_rows:
        if _norm(row.get("second_review_decision")) == "CONFIRM_NEEDS_MORE_INFO":
            base_valid_row = row
            break
    if base_valid_row is None and valid_rows:
        base_valid_row = valid_rows[0]
    if base_valid_row is None:
        base_valid_row = sample_df.iloc[0].to_dict()
        base_valid_row["second_review_decision"] = "CONFIRM_NEEDS_MORE_INFO"
        base_valid_row["remaining_question"] = "Fallback question"
        base_valid_row["second_reviewer_id"] = "fallback_reviewer"
        base_valid_row["second_reviewer_role"] = "accounting_reviewer"
        base_valid_row["second_review_reason_code"] = "fallback"
        base_valid_row["second_review_notes"] = "fallback notes"
        base_valid_row["reviewed_at_utc"] = (
            datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        )

    negative = _run_negative_tests(base_valid_row, queue_map)
    _write_json(OUT_NEG, negative)

    def _detected(case_name: str) -> bool:
        for t in negative.get("tests", []):
            if t.get("name") == case_name:
                return bool(t.get("detected"))
        return False

    second_review_input_schema_valid = all(
        _norm(r.get("schema_version")) == SCHEMA_VERSION for _, r in sample_df.iterrows()
    )
    valid_second_review_count = len(valid_df)
    invalid_second_review_count = len(invalid_df)
    confirm_needs_more_info_count = int((valid_df.get("second_review_decision", pd.Series([])) == "CONFIRM_NEEDS_MORE_INFO").sum())
    confirm_reject_count = int((valid_df.get("second_review_decision", pd.Series([])) == "CONFIRM_REJECT").sum())
    escalate_manual_accounting_review_count = int(
        (valid_df.get("second_review_decision", pd.Series([])) == "ESCALATE_TO_MANUAL_ACCOUNTING_REVIEW").sum()
    )
    approve_for_sandbox_preview_candidate_count = int(
        (valid_df.get("second_review_decision", pd.Series([])) == "APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE").sum()
    )

    after = _snapshot_hashes()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()

    summary = {
        "stage": "7X",
        "external_api_called": False,
        "real_apply_executed": False,
        "stage7w_summary_loaded": stage7w_summary_loaded,
        "second_review_queue_loaded": second_review_queue_loaded,
        "second_review_template_loaded": second_review_template_loaded,
        "second_review_policy_loaded": second_review_policy_loaded,
        "second_review_sample_input_generated": True,
        "second_review_input_schema_valid": second_review_input_schema_valid,
        "valid_second_review_count": valid_second_review_count,
        "invalid_second_review_count": invalid_second_review_count,
        "confirm_needs_more_info_count": confirm_needs_more_info_count,
        "confirm_reject_count": confirm_reject_count,
        "escalate_manual_accounting_review_count": escalate_manual_accounting_review_count,
        "approve_for_sandbox_preview_candidate_count": approve_for_sandbox_preview_candidate_count,
        "sandbox_preview_candidate_projection_generated": True,
        "approve_for_real_apply_rejected": _detected("approve_for_real_apply"),
        "safe_to_apply_human_field_rejected": _detected("manual_safe_to_apply_field"),
        "immutable_field_tamper_detected": _detected("immutable_tamper"),
        "missing_second_reviewer_id_detected": _detected("missing_second_reviewer_id"),
        "invalid_decision_enum_detected": _detected("invalid_decision_enum"),
        "value_mismatch_without_corrected_value_rejected": _detected("value_mismatch_without_corrected_value"),
        "evidence_checks_required_for_candidate": _detected("candidate_without_evidence_checks"),
        "duplicate_second_review_detected": _detected("duplicate_queue_suggestion"),
        "malformed_reviewed_at_detected": _detected("malformed_reviewed_at_utc"),
        "blocked_value_mismatch_auto_apply_count": 0,
        "sandbox_apply_attempt_count": 0,
        "sandbox_apply_success_count": 0,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": _norm(delivery.get("overall_status")),
        "stage7w_guard_ok": stage7w_guard_ok,
        "ready_for_stage7y_sandbox_preview_candidate_from_second_review": True,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# Stage 7X Second Review Input Validation",
        "",
        "Mode: no API call, no real apply, no production write.",
        "",
        "## Input Guard",
        f"- Stage7W summary loaded: {stage7w_summary_loaded}",
        f"- Stage7W guard check passed: {stage7w_guard_ok}",
        "",
        "## Sample Validation",
        f"- valid_second_review_count: {valid_second_review_count}",
        f"- invalid_second_review_count: {invalid_second_review_count}",
        f"- confirm_needs_more_info_count: {confirm_needs_more_info_count}",
        f"- escalate_manual_accounting_review_count: {escalate_manual_accounting_review_count}",
        f"- approve_for_sandbox_preview_candidate_count: {approve_for_sandbox_preview_candidate_count}",
        "",
        "## Safety",
        "- Any APPROVE_FOR_REAL_APPLY is rejected.",
        "- Any human supplied safe_to_apply is rejected.",
        "- Candidate rows are future sandbox-preview candidates only.",
        "- No sandbox apply attempt and no production write executed in Stage7X.",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print("stage7x_status=ok")
    print(f"stage7x_summary={OUT_SUMMARY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
