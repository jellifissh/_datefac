import copy
import hashlib
import json
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
IN_DIR = BASE_DIR / "output" / "stage7t_real_human_approval_input_design"

IN_SCHEMA = IN_DIR / "207_stage7t_real_human_approval_input_schema.json"
IN_RULES = IN_DIR / "207_stage7t_real_human_approval_validation_rules.json"
IN_TEMPLATE_CSV = IN_DIR / "207_stage7t_real_human_approval_input_template.csv"
IN_TEMPLATE_JSONL = IN_DIR / "207_stage7t_real_human_approval_input_template.jsonl"
IN_SAMPLE_CSV = IN_DIR / "207_stage7t_real_human_approval_sample_input.csv"
IN_BLOCKED_PROOF = IN_DIR / "207_stage7t_blocked_value_mismatch_proof.json"
IN_SUMMARY = IN_DIR / "207_stage7t_real_human_approval_input_summary.json"

OUT_DIR = BASE_DIR / "output" / "stage7u_real_human_approval_validation"
OUT_SUMMARY = OUT_DIR / "208_stage7u_real_human_approval_validation_summary.json"
OUT_REPORT = OUT_DIR / "208_stage7u_real_human_approval_validation_report.md"
OUT_VALID = OUT_DIR / "208_stage7u_validated_approval_results.xlsx"
OUT_INVALID = OUT_DIR / "208_stage7u_invalid_approval_results.xlsx"
OUT_AUDIT = OUT_DIR / "208_stage7u_validation_audit.xlsx"
OUT_NEG = OUT_DIR / "208_stage7u_negative_validation_tests.json"
OUT_PROJECTION = OUT_DIR / "208_stage7u_sandbox_preview_candidate_projection.xlsx"

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


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _sha256(path: Path) -> str:
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


def _hash_value(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        try:
            if pd.isna(v):
                return ""
        except Exception:
            pass
        return str(v)
    return _norm(v)


def _recompute_hash(row: Dict[str, Any], immutable_fields_without_hash: List[str]) -> str:
    payload = {k: _hash_value(row.get(k, "")) for k in immutable_fields_without_hash}
    serial = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(serial.encode("utf-8")).hexdigest()


def _parse_datetime_ok(v: str) -> bool:
    t = _norm(v)
    if not t:
        return False
    try:
        datetime.fromisoformat(t.replace("Z", "+00:00"))
        return True
    except Exception:
        return False


def _validate_row(
    row: Dict[str, Any],
    original_map: Dict[Tuple[str, str], Dict[str, Any]],
    immutable_fields: List[str],
    immutable_without_hash: List[str],
    allowed_decisions: List[str],
    seen_queue: set,
    seen_suggestion: set,
) -> List[str]:
    errors: List[str] = []

    queue_item_id = _norm(row.get("queue_item_id"))
    suggestion_id = _norm(row.get("suggestion_id"))
    schema_version = _norm(row.get("schema_version"))
    reviewer_id = _norm(row.get("reviewer_id"))
    reviewer_role = _norm(row.get("reviewer_role"))
    human_decision = _norm(row.get("human_decision"))
    reviewer_notes = _norm(row.get("reviewer_notes"))
    reviewed_at_utc = _norm(row.get("reviewed_at_utc"))

    if schema_version != "stage7t_real_human_approval_input_v1":
        errors.append("schema_version_invalid")
    if not queue_item_id:
        errors.append("queue_item_id_missing")
    if not suggestion_id:
        errors.append("suggestion_id_missing")
    if queue_item_id in seen_queue:
        errors.append("duplicate_queue_item_id")
    else:
        seen_queue.add(queue_item_id)
    if suggestion_id in seen_suggestion:
        errors.append("duplicate_suggestion_id")
    else:
        seen_suggestion.add(suggestion_id)
    if not reviewer_id:
        errors.append("reviewer_id_missing")
    if not reviewer_role:
        errors.append("reviewer_role_missing")
    if not human_decision:
        errors.append("human_decision_missing")
    if human_decision not in set(allowed_decisions):
        errors.append("invalid_human_decision_enum")
    if human_decision in {"APPROVE_FOR_REAL_APPLY", "SAFE_TO_APPLY"}:
        errors.append("forbidden_human_decision")
    if not reviewer_notes:
        errors.append("reviewer_notes_missing")
    if not _parse_datetime_ok(reviewed_at_utc):
        errors.append("reviewed_at_utc_invalid")

    original = original_map.get((queue_item_id, suggestion_id))
    if original is None:
        errors.append("original_queue_item_not_found")
    else:
        for f in immutable_fields:
            if f == "immutable_row_hash":
                continue
            if _norm(row.get(f)) != _norm(original.get(f)):
                errors.append(f"immutable_field_changed:{f}")
        if _norm(row.get("immutable_row_hash")) != _norm(original.get("immutable_row_hash")):
            errors.append("immutable_row_hash_changed")
        recomputed = _recompute_hash(row, immutable_without_hash)
        if _norm(row.get("immutable_row_hash")) != recomputed:
            errors.append("immutable_row_hash_recompute_mismatch")

    value_mismatch = _as_bool(row.get("value_mismatch"))
    conflict_type = _norm(row.get("conflict_type"))
    prior_stage_status = _norm(row.get("prior_stage_status")).lower()
    corrected_filled = any(
        _norm(row.get(x))
        for x in ["corrected_metric_name", "corrected_value", "corrected_unit", "corrected_fiscal_year"]
    )

    if human_decision == "APPROVE_FOR_SANDBOX_PREVIEW":
        for flag in ["evidence_checked", "source_row_confirmed", "fiscal_year_confirmed", "unit_confirmed", "value_confirmed"]:
            if not _as_bool(row.get(flag)):
                errors.append(f"approve_missing_required_flag:{flag}")
        if value_mismatch:
            errors.append("approve_forbidden_value_mismatch")
        if "true_value_conflict" in conflict_type:
            errors.append("approve_forbidden_true_value_conflict")
        if "blocked_apply" in prior_stage_status or "unresolved_conflict" in prior_stage_status:
            errors.append("approve_forbidden_prior_stage_blocked")
        if corrected_filled:
            errors.append("approve_forbidden_corrected_fields_filled")

    if human_decision == "REJECT":
        if not _norm(row.get("decision_reason_code")):
            errors.append("reject_missing_decision_reason_code")
        if not reviewer_notes:
            errors.append("reject_missing_reviewer_notes")

    if human_decision == "NEEDS_MORE_INFO":
        if not _norm(row.get("needs_more_info_question")):
            errors.append("needs_more_info_missing_question")
        if not reviewer_notes:
            errors.append("needs_more_info_missing_reviewer_notes")

    if human_decision == "REQUIRE_SECOND_REVIEW":
        if not _as_bool(row.get("second_review_required")):
            errors.append("second_review_flag_required")
        if not reviewer_notes:
            errors.append("second_review_missing_reviewer_notes")
        if _norm(row.get("second_reviewer_id")) and not _norm(row.get("second_review_notes")):
            errors.append("second_review_notes_required_when_second_reviewer_present")

    if value_mismatch or "true_value_conflict" in conflict_type:
        if human_decision not in {"NEEDS_MORE_INFO", "REQUIRE_SECOND_REVIEW"}:
            errors.append("mismatch_or_true_conflict_must_not_be_approved")

    return errors


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    required = [
        IN_SCHEMA,
        IN_RULES,
        IN_TEMPLATE_CSV,
        IN_TEMPLATE_JSONL,
        IN_SAMPLE_CSV,
        IN_BLOCKED_PROOF,
        IN_SUMMARY,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "7U",
                "external_api_called": False,
                "real_apply_executed": False,
                "approval_input_loaded": False,
                "blocked": True,
                "blocked_reason": f"missing_input:{'|'.join(missing)}",
            },
        )
        print("stage7u_status=blocked_missing_input")
        return 0

    before = _snapshot_hashes()

    schema = _load_json(IN_SCHEMA)
    rules = _load_json(IN_RULES)
    _ = _load_json(IN_BLOCKED_PROOF)
    _ = _load_json(IN_SUMMARY)
    template_df = pd.read_csv(IN_TEMPLATE_CSV)
    template_jsonl = _load_jsonl(IN_TEMPLATE_JSONL)
    sample_df = pd.read_csv(IN_SAMPLE_CSV)

    approval_input_loaded = len(sample_df) > 0
    validation_rules_loaded = bool(rules)
    immutable_fields = schema.get("immutable_fields", [])
    immutable_without_hash = [x for x in immutable_fields if x != "immutable_row_hash"]
    allowed_decisions = schema.get("human_decision_enum", [])
    approval_input_schema_valid = (
        schema.get("schema_version") == "stage7t_real_human_approval_input_v1"
        and "immutable_fields" in schema
        and "human_fillable_fields" in schema
        and "human_decision_enum" in schema
        and len(template_df) == len(template_jsonl)
    )

    # Build original immutable source from template csv.
    template_rows = [r for _, r in template_df.iterrows()]
    original_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for r in template_rows:
        d = r.to_dict()
        key = (_norm(d.get("queue_item_id")), _norm(d.get("suggestion_id")))
        original_map[key] = d

    seen_queue: set = set()
    seen_suggestion: set = set()
    audit_rows: List[Dict[str, Any]] = []
    valid_rows: List[Dict[str, Any]] = []
    invalid_rows: List[Dict[str, Any]] = []
    sandbox_projection_rows: List[Dict[str, Any]] = []
    blocked_value_mismatch_auto_apply_count = 0
    needs_more_info_count = 0
    require_second_review_count = 0
    sandbox_preview_candidate_count = 0

    for _, sr in sample_df.iterrows():
        row = sr.to_dict()
        errors = _validate_row(
            row,
            original_map,
            immutable_fields,
            immutable_without_hash,
            allowed_decisions,
            seen_queue,
            seen_suggestion,
        )
        decision = _norm(row.get("human_decision"))
        value_mismatch = _as_bool(row.get("value_mismatch"))
        row_valid = len(errors) == 0

        if decision == "NEEDS_MORE_INFO":
            needs_more_info_count += 1
        if decision == "REQUIRE_SECOND_REVIEW":
            require_second_review_count += 1
        if decision == "APPROVE_FOR_SANDBOX_PREVIEW" and row_valid:
            sandbox_preview_candidate_count += 1
            if value_mismatch:
                blocked_value_mismatch_auto_apply_count += 1

        record = dict(row)
        record["validation_errors"] = "|".join(errors)
        record["row_valid"] = row_valid
        if row_valid:
            valid_rows.append(record)
        else:
            invalid_rows.append(record)

        audit_rows.append(
            {
                "queue_item_id": _norm(row.get("queue_item_id")),
                "suggestion_id": _norm(row.get("suggestion_id")),
                "human_decision": decision,
                "value_mismatch": value_mismatch,
                "row_valid": row_valid,
                "error_count": len(errors),
                "validation_errors": "|".join(errors),
            }
        )
        sandbox_projection_rows.append(
            {
                "queue_item_id": _norm(row.get("queue_item_id")),
                "suggestion_id": _norm(row.get("suggestion_id")),
                "human_decision": decision,
                "row_valid": row_valid,
                "value_mismatch": value_mismatch,
                "sandbox_preview_candidate": row_valid and decision == "APPROVE_FOR_SANDBOX_PREVIEW" and (not value_mismatch),
            }
        )

    pd.DataFrame(valid_rows).to_excel(OUT_VALID, sheet_name="validated_approval_results", index=False, engine="openpyxl")
    pd.DataFrame(invalid_rows).to_excel(OUT_INVALID, sheet_name="invalid_approval_results", index=False, engine="openpyxl")
    pd.DataFrame(audit_rows).to_excel(OUT_AUDIT, sheet_name="validation_audit", index=False, engine="openpyxl")
    pd.DataFrame(sandbox_projection_rows).to_excel(OUT_PROJECTION, sheet_name="candidate_projection", index=False, engine="openpyxl")

    # Negative tests
    if len(sample_df) == 0:
        base_row = {}
    else:
        base_row = sample_df.iloc[0].to_dict()

    def make_test_row(mut: Dict[str, Any]) -> Dict[str, Any]:
        r = copy.deepcopy(base_row)
        for k, v in mut.items():
            r[k] = v
        return r

    negative_cases = []
    # 1 missing reviewer_id
    negative_cases.append(("missing_reviewer_id", make_test_row({"reviewer_id": ""}), "reviewer_id_missing"))
    # 2 invalid enum
    negative_cases.append(("invalid_decision_enum", make_test_row({"human_decision": "INVALID_DECISION"}), "invalid_human_decision_enum"))
    # 3 immutable field tamper
    negative_cases.append(("immutable_field_tamper", make_test_row({"source_page": 999}), "immutable_field_changed:source_page"))
    # 4 hash mismatch
    negative_cases.append(("immutable_hash_mismatch", make_test_row({"immutable_row_hash": "abc123"}), "immutable_row_hash_changed"))
    # 5 approve with value_mismatch true
    negative_cases.append(
        (
            "approve_with_value_mismatch",
            make_test_row(
                {
                    "human_decision": "APPROVE_FOR_SANDBOX_PREVIEW",
                    "value_mismatch": True,
                    "evidence_checked": True,
                    "source_row_confirmed": True,
                    "fiscal_year_confirmed": True,
                    "unit_confirmed": True,
                    "value_confirmed": True,
                }
            ),
            "approve_forbidden_value_mismatch",
        )
    )
    # 6 approve with corrected_value filled
    negative_cases.append(
        (
            "approve_with_corrected_value",
            make_test_row(
                {
                    "human_decision": "APPROVE_FOR_SANDBOX_PREVIEW",
                    "value_mismatch": False,
                    "evidence_checked": True,
                    "source_row_confirmed": True,
                    "fiscal_year_confirmed": True,
                    "unit_confirmed": True,
                    "value_confirmed": True,
                    "corrected_value": "123.45",
                }
            ),
            "approve_forbidden_corrected_fields_filled",
        )
    )
    # 7 duplicate suggestion_id (two-row scenario)
    # handled separately below
    # 8 direct approve for real apply
    negative_cases.append(("approve_for_real_apply_attempt", make_test_row({"human_decision": "APPROVE_FOR_REAL_APPLY"}), "invalid_human_decision_enum"))

    neg_results: List[Dict[str, Any]] = []
    immut_tamper_detected = False
    immut_hash_mismatch_detected = False
    invalid_enum_detected = False
    value_mismatch_approve_rejected = False
    corrected_value_approve_rejected = False
    approve_for_real_apply_rejected = False

    for case_name, row, expect_err in negative_cases:
        seen_q = set()
        seen_s = set()
        errs = _validate_row(
            row,
            original_map,
            immutable_fields,
            immutable_without_hash,
            allowed_decisions,
            seen_q,
            seen_s,
        )
        hit = expect_err in errs
        neg_results.append(
            {
                "case": case_name,
                "expected_error": expect_err,
                "errors": errs,
                "detected": hit,
            }
        )
        if case_name == "immutable_field_tamper" and hit:
            immut_tamper_detected = True
        if case_name == "immutable_hash_mismatch" and hit:
            immut_hash_mismatch_detected = True
        if case_name == "invalid_decision_enum" and hit:
            invalid_enum_detected = True
        if case_name == "approve_with_value_mismatch" and hit:
            value_mismatch_approve_rejected = True
        if case_name == "approve_with_corrected_value" and hit:
            corrected_value_approve_rejected = True
        if case_name == "approve_for_real_apply_attempt" and hit:
            approve_for_real_apply_rejected = True

    # duplicate suggestion_id test with two rows
    duplicate_row_a = copy.deepcopy(sample_df.iloc[0].to_dict())
    duplicate_row_b = copy.deepcopy(sample_df.iloc[1].to_dict()) if len(sample_df) > 1 else copy.deepcopy(sample_df.iloc[0].to_dict())
    duplicate_row_b["suggestion_id"] = duplicate_row_a.get("suggestion_id")
    duplicate_row_b["queue_item_id"] = _norm(duplicate_row_b.get("queue_item_id")) + "_DIFF"
    seen_q = set()
    seen_s = set()
    errs_a = _validate_row(duplicate_row_a, original_map, immutable_fields, immutable_without_hash, allowed_decisions, seen_q, seen_s)
    errs_b = _validate_row(duplicate_row_b, original_map, immutable_fields, immutable_without_hash, allowed_decisions, seen_q, seen_s)
    dup_detected = "duplicate_suggestion_id" in errs_b
    neg_results.append(
        {
            "case": "duplicate_suggestion_id",
            "expected_error": "duplicate_suggestion_id",
            "errors_first": errs_a,
            "errors_second": errs_b,
            "detected": dup_detected,
        }
    )

    _write_json(OUT_NEG, {"negative_tests": neg_results})

    valid_approval_count = len(valid_rows)
    invalid_approval_count = len(invalid_rows)

    after = _snapshot_hashes()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]
    delivery = _run_delivery_check()
    check_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "7U",
        "external_api_called": False,
        "real_apply_executed": False,
        "approval_input_loaded": approval_input_loaded,
        "approval_input_schema_valid": approval_input_schema_valid,
        "validation_rules_loaded": validation_rules_loaded,
        "immutable_field_validation_enabled": True,
        "immutable_field_tamper_detected": immut_tamper_detected,
        "immutable_row_hash_mismatch_detected": immut_hash_mismatch_detected,
        "invalid_decision_enum_detected": invalid_enum_detected,
        "duplicate_suggestion_id_detected": dup_detected,
        "value_mismatch_approve_rejected": value_mismatch_approve_rejected,
        "corrected_value_approve_rejected": corrected_value_approve_rejected,
        "approve_for_real_apply_rejected": approve_for_real_apply_rejected,
        "blocked_value_mismatch_auto_apply_count": blocked_value_mismatch_auto_apply_count,
        "valid_approval_count": valid_approval_count,
        "invalid_approval_count": invalid_approval_count,
        "needs_more_info_count": needs_more_info_count,
        "require_second_review_count": require_second_review_count,
        "sandbox_preview_candidate_count": sandbox_preview_candidate_count,
        "ready_for_stage7v_sandbox_preview_from_validated_real_human_approval": bool(
            approval_input_loaded
            and approval_input_schema_valid
            and validation_rules_loaded
            and immut_tamper_detected
            and immut_hash_mismatch_detected
            and invalid_enum_detected
            and dup_detected
            and value_mismatch_approve_rejected
            and corrected_value_approve_rejected
            and approve_for_real_apply_rejected
            and blocked_value_mismatch_auto_apply_count == 0
            and check_status == "PASS"
        ),
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": check_status,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# Stage7U Real Human Approval Validation",
        "",
        "No external API call; no real apply; no production write.",
        "",
        "## Input",
        f"- approval_input_loaded: {summary['approval_input_loaded']}",
        f"- approval_input_schema_valid: {summary['approval_input_schema_valid']}",
        f"- validation_rules_loaded: {summary['validation_rules_loaded']}",
        "",
        "## Core Validation",
        f"- valid_approval_count: {summary['valid_approval_count']}",
        f"- invalid_approval_count: {summary['invalid_approval_count']}",
        f"- needs_more_info_count: {summary['needs_more_info_count']}",
        f"- require_second_review_count: {summary['require_second_review_count']}",
        f"- sandbox_preview_candidate_count: {summary['sandbox_preview_candidate_count']}",
        "",
        "## Negative Tests",
        f"- immutable_field_tamper_detected: {summary['immutable_field_tamper_detected']}",
        f"- immutable_row_hash_mismatch_detected: {summary['immutable_row_hash_mismatch_detected']}",
        f"- invalid_decision_enum_detected: {summary['invalid_decision_enum_detected']}",
        f"- duplicate_suggestion_id_detected: {summary['duplicate_suggestion_id_detected']}",
        f"- value_mismatch_approve_rejected: {summary['value_mismatch_approve_rejected']}",
        f"- corrected_value_approve_rejected: {summary['corrected_value_approve_rejected']}",
        f"- approve_for_real_apply_rejected: {summary['approve_for_real_apply_rejected']}",
        "",
        "## Safety",
        f"- blocked_value_mismatch_auto_apply_count: {summary['blocked_value_mismatch_auto_apply_count']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        "",
        "## Decision",
        f"- ready_for_stage7v_sandbox_preview_from_validated_real_human_approval: {summary['ready_for_stage7v_sandbox_preview_from_validated_real_human_approval']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"stage7u_external_api_called={str(summary['external_api_called']).lower()}")
    print(f"stage7u_real_apply_executed={str(summary['real_apply_executed']).lower()}")
    print(f"stage7u_approval_input_loaded={str(summary['approval_input_loaded']).lower()}")
    print(f"stage7u_valid_approval_count={summary['valid_approval_count']}")
    print(f"stage7u_invalid_approval_count={summary['invalid_approval_count']}")
    print(f"stage7u_blocked_value_mismatch_auto_apply_count={summary['blocked_value_mismatch_auto_apply_count']}")
    print(f"stage7u_check_delivery_state={summary['check_delivery_state_overall_status']}")
    print(
        "stage7u_ready_for_stage7v="
        f"{str(summary['ready_for_stage7v_sandbox_preview_from_validated_real_human_approval']).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
