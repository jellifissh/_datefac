import hashlib
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

IN_STAGE7P_SUMMARY = BASE_DIR / "output" / "stage7p_ai_suggestion_queue_integration" / "203_stage7p_ai_suggestion_queue_summary.json"
IN_STAGE7P_QUEUE = BASE_DIR / "output" / "stage7p_ai_suggestion_queue_integration" / "203_stage7p_ai_suggestion_queue.xlsx"
IN_STAGE7Q_APPROVED = BASE_DIR / "output" / "stage7q_human_approval_flow_design" / "204_stage7q_approved_suggestions.xlsx"
IN_STAGE7Q_REJECTED = BASE_DIR / "output" / "stage7q_human_approval_flow_design" / "204_stage7q_rejected_by_human.xlsx"
IN_STAGE7Q_NEEDS_INFO = BASE_DIR / "output" / "stage7q_human_approval_flow_design" / "204_stage7q_needs_more_info_queue.xlsx"
IN_STAGE7R_SUMMARY = BASE_DIR / "output" / "stage7r_human_approval_sandbox_apply_preview" / "205_stage7r_sandbox_apply_preview_summary.json"
IN_STAGE7R_BLOCKED = BASE_DIR / "output" / "stage7r_human_approval_sandbox_apply_preview" / "205_stage7r_blocked_apply_preview.xlsx"
IN_STAGE7S_SUMMARY = BASE_DIR / "output" / "stage7s_blocked_approved_suggestion_review" / "206_stage7s_blocked_review_summary.json"
IN_STAGE7S_REVIEW = BASE_DIR / "output" / "stage7s_blocked_approved_suggestion_review" / "206_stage7s_blocked_suggestion_review.xlsx"
IN_STAGE7G_PREVIEW = BASE_DIR / "output" / "stage7g_manual_review_reduction_sandbox" / "186_stage7g_reduced_clean_06_preview.xlsx"
IN_STAGE7G_REMAINING = BASE_DIR / "output" / "stage7g_manual_review_reduction_sandbox" / "186_stage7g_remaining_manual_review.xlsx"

OUT_DIR = BASE_DIR / "output" / "stage7t_real_human_approval_input_design"
OUT_SUMMARY = OUT_DIR / "207_stage7t_real_human_approval_input_summary.json"
OUT_REPORT = OUT_DIR / "207_stage7t_real_human_approval_design_report.md"
OUT_SCHEMA = OUT_DIR / "207_stage7t_real_human_approval_input_schema.json"
OUT_TEMPLATE_CSV = OUT_DIR / "207_stage7t_real_human_approval_input_template.csv"
OUT_TEMPLATE_JSONL = OUT_DIR / "207_stage7t_real_human_approval_input_template.jsonl"
OUT_VALIDATION_RULES = OUT_DIR / "207_stage7t_real_human_approval_validation_rules.json"
OUT_SAMPLE_INPUT_CSV = OUT_DIR / "207_stage7t_real_human_approval_sample_input.csv"
OUT_VALIDATION_AUDIT = OUT_DIR / "207_stage7t_real_human_approval_validation_audit.xlsx"
OUT_BLOCKED_PROOF = OUT_DIR / "207_stage7t_blocked_value_mismatch_proof.json"
OUT_CANDIDATE_PROJECTION = OUT_DIR / "207_stage7t_sandbox_preview_candidate_projection.xlsx"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

SCHEMA_VERSION = "stage7t_real_human_approval_input_v1"
ALLOWED_DECISIONS = {
    "APPROVE_FOR_SANDBOX_PREVIEW",
    "REJECT",
    "NEEDS_MORE_INFO",
    "REQUIRE_SECOND_REVIEW",
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
    "duplicate_key",
    "eps_related",
    "ai_confidence",
    "ai_rationale",
    "prior_stage_status",
]

HUMAN_FILLABLE_FIELDS = [
    "schema_version",
    "reviewer_id",
    "reviewer_role",
    "human_decision",
    "decision_reason_code",
    "reviewer_notes",
    "evidence_checked",
    "source_row_confirmed",
    "fiscal_year_confirmed",
    "unit_confirmed",
    "value_confirmed",
    "corrected_metric_name",
    "corrected_value",
    "corrected_unit",
    "corrected_fiscal_year",
    "needs_more_info_question",
    "second_review_required",
    "second_reviewer_id",
    "second_review_notes",
    "reviewed_at_utc",
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


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _parse_key(key: str) -> Tuple[str, str, str]:
    parts = key.split("||")
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]
    return "", "", ""


def _is_eps(metric: str) -> bool:
    t = metric.lower()
    return "eps" in t or "每股收益" in metric


def _immutable_hash(row: Dict[str, Any]) -> str:
    payload = {k: row.get(k, "") for k in IMMUTABLE_FIELDS}
    serial = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(serial.encode("utf-8")).hexdigest()


def _ensure_bool_str(v: bool) -> str:
    return "true" if v else "false"


def _parse_datetime_ok(v: str) -> bool:
    t = _norm(v)
    if not t:
        return False
    try:
        # Support both ISO and "YYYY-MM-DD HH:MM:SS"
        datetime.fromisoformat(t.replace("Z", "+00:00"))
        return True
    except Exception:
        return False


def _validate_row(
    row: Dict[str, Any],
    original_map: Dict[Tuple[str, str], Dict[str, Any]],
    seen_keys: set,
) -> List[str]:
    errors: List[str] = []
    queue_item_id = _norm(row.get("queue_item_id"))
    suggestion_id = _norm(row.get("suggestion_id"))
    dedup_key = (queue_item_id, suggestion_id)
    if dedup_key in seen_keys:
        errors.append("duplicate_queue_item_id_or_suggestion_id")
    else:
        seen_keys.add(dedup_key)

    if _norm(row.get("schema_version")) != SCHEMA_VERSION:
        errors.append("schema_version_invalid")
    if not queue_item_id:
        errors.append("queue_item_id_missing")
    if not suggestion_id:
        errors.append("suggestion_id_missing")
    if not _norm(row.get("reviewer_id")):
        errors.append("reviewer_id_missing")
    if not _norm(row.get("reviewer_role")):
        errors.append("reviewer_role_missing")
    decision = _norm(row.get("human_decision"))
    if decision not in ALLOWED_DECISIONS:
        errors.append("human_decision_invalid")
    if not _norm(row.get("reviewer_notes")):
        errors.append("reviewer_notes_missing")
    if not _parse_datetime_ok(_norm(row.get("reviewed_at_utc"))):
        errors.append("reviewed_at_utc_invalid")

    # Immutable fields unchanged + hash match
    original = original_map.get((queue_item_id, suggestion_id))
    if original is None:
        errors.append("original_queue_item_not_found")
    else:
        for k in IMMUTABLE_FIELDS:
            if _norm(row.get(k)) != _norm(original.get(k)):
                errors.append(f"immutable_field_changed:{k}")
        if _norm(row.get("immutable_row_hash")) != _norm(original.get("immutable_row_hash")):
            errors.append("immutable_row_hash_mismatch")
        if _norm(row.get("immutable_row_hash")) != _immutable_hash(original):
            errors.append("immutable_row_hash_recompute_mismatch")

    value_mismatch = _as_bool(row.get("value_mismatch"))
    conflict_type = _norm(row.get("conflict_type"))
    prior_stage_status = _norm(row.get("prior_stage_status"))

    corrected_fields_filled = any(
        _norm(row.get(x))
        for x in ["corrected_metric_name", "corrected_value", "corrected_unit", "corrected_fiscal_year"]
    )

    if decision == "APPROVE_FOR_SANDBOX_PREVIEW":
        if not _as_bool(row.get("evidence_checked")):
            errors.append("approve_requires_evidence_checked")
        if not _as_bool(row.get("source_row_confirmed")):
            errors.append("approve_requires_source_row_confirmed")
        if not _as_bool(row.get("fiscal_year_confirmed")):
            errors.append("approve_requires_fiscal_year_confirmed")
        if not _as_bool(row.get("unit_confirmed")):
            errors.append("approve_requires_unit_confirmed")
        if not _as_bool(row.get("value_confirmed")):
            errors.append("approve_requires_value_confirmed")
        if value_mismatch:
            errors.append("approve_forbidden_value_mismatch")
        if "true_value_conflict" in conflict_type:
            errors.append("approve_forbidden_true_value_conflict")
        if "blocked_apply" in prior_stage_status or "unresolved_conflict" in prior_stage_status:
            errors.append("approve_forbidden_prior_stage_blocked")
        if corrected_fields_filled:
            errors.append("approve_forbidden_when_corrected_fields_filled")

    if decision == "REJECT":
        if not _norm(row.get("decision_reason_code")):
            errors.append("reject_requires_decision_reason_code")
        if not _norm(row.get("reviewer_notes")):
            errors.append("reject_requires_reviewer_notes")

    if decision == "NEEDS_MORE_INFO":
        if not _norm(row.get("needs_more_info_question")):
            errors.append("needs_more_info_requires_question")
        if not _norm(row.get("reviewer_notes")):
            errors.append("needs_more_info_requires_reviewer_notes")

    if decision == "REQUIRE_SECOND_REVIEW":
        if not _as_bool(row.get("second_review_required")):
            errors.append("second_review_requires_flag_true")
        if not _norm(row.get("reviewer_notes")):
            errors.append("second_review_requires_notes")
        if _norm(row.get("second_reviewer_id")) and not _norm(row.get("second_review_notes")):
            errors.append("second_reviewer_id_requires_second_review_notes")

    # Strong safety force for mismatch/true conflict
    if value_mismatch or "true_value_conflict" in conflict_type:
        if decision not in {"NEEDS_MORE_INFO", "REQUIRE_SECOND_REVIEW"}:
            errors.append("value_mismatch_or_true_conflict_must_not_be_approved_or_rejected_directly")

    return errors


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    required = [
        IN_STAGE7P_SUMMARY,
        IN_STAGE7P_QUEUE,
        IN_STAGE7Q_APPROVED,
        IN_STAGE7Q_REJECTED,
        IN_STAGE7Q_NEEDS_INFO,
        IN_STAGE7R_SUMMARY,
        IN_STAGE7R_BLOCKED,
        IN_STAGE7S_SUMMARY,
        IN_STAGE7S_REVIEW,
        IN_STAGE7G_PREVIEW,
        IN_STAGE7G_REMAINING,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "7T",
                "external_api_called": False,
                "blocked": True,
                "blocked_reason": f"missing_input:{'|'.join(missing)}",
            },
        )
        print("stage7t_status=blocked_missing_input")
        return 0

    before = _snapshot_hashes()

    queue_df = pd.read_excel(IN_STAGE7P_QUEUE)
    _ = _load_json(IN_STAGE7P_SUMMARY)
    _ = pd.read_excel(IN_STAGE7Q_APPROVED)
    _ = pd.read_excel(IN_STAGE7Q_REJECTED)
    _ = pd.read_excel(IN_STAGE7Q_NEEDS_INFO)
    _ = _load_json(IN_STAGE7R_SUMMARY)
    blocked_df = pd.read_excel(IN_STAGE7R_BLOCKED)
    _ = _load_json(IN_STAGE7S_SUMMARY)
    _ = pd.read_excel(IN_STAGE7S_REVIEW)
    clean_preview_df = pd.read_excel(IN_STAGE7G_PREVIEW)
    remaining_df = pd.read_excel(IN_STAGE7G_REMAINING)

    blocked_key_set = {(_norm(r.get("queue_id")), _norm(r.get("review_id"))) for _, r in blocked_df.iterrows()}
    blocked_reason_map = {
        (_norm(r.get("queue_id")), _norm(r.get("review_id"))): _norm(r.get("block_reasons"))
        for _, r in blocked_df.iterrows()
    }

    template_rows: List[Dict[str, Any]] = []
    for _, q in queue_df.iterrows():
        queue_id = _norm(q.get("queue_id"))
        review_id = _norm(q.get("review_id"))
        key = (_norm(queue_id), _norm(review_id))
        original_request_id = _norm(q.get("original_request_id"))
        asset_package, metric_key, year_key = _parse_key(original_request_id)
        metric = _norm(q.get("suggested_metric_name")) or metric_key
        year = _norm(q.get("suggested_year")) or year_key

        rem = remaining_df[remaining_df["analysis_key"].astype(str) == original_request_id] if "analysis_key" in remaining_df.columns else pd.DataFrame()
        clean = clean_preview_df[
            (clean_preview_df["asset_package"].astype(str) == asset_package)
            & (clean_preview_df["standard_metric"].astype(str) == metric)
            & (clean_preview_df["year"].astype(str) == year)
        ]

        source_pdf = _norm(rem.iloc[0].get("source_pdf")) if len(rem) == 1 else (_norm(clean.iloc[0].get("source_pdf")) if len(clean) == 1 else "")
        source_page = _norm(rem.iloc[0].get("page_number")) if len(rem) == 1 else (_norm(clean.iloc[0].get("page_number")) if len(clean) == 1 else "")
        statement_type = _norm(rem.iloc[0].get("statement_type")) if len(rem) == 1 else (_norm(clean.iloc[0].get("statement_type")) if len(clean) == 1 else "")
        original_metric_name = _norm(rem.iloc[0].get("raw_metric_name")) if len(rem) == 1 else _norm(clean.iloc[0].get("raw_metric_name")) if len(clean) == 1 else ""
        existing_metric_name = _norm(clean.iloc[0].get("standard_metric")) if len(clean) == 1 else metric
        existing_value = _norm(clean.iloc[0].get("final_value")) if len(clean) == 1 else ""
        existing_unit = _norm(clean.iloc[0].get("final_unit")) if len(clean) == 1 else ""
        conflict_type = _norm(clean.iloc[0].get("conflict_category")) if len(clean) == 1 else "unknown_conflict"
        duplicate_key = len(clean) > 1
        # Stage7T keeps value_mismatch aligned with Stage7R/7S blocked evidence,
        # instead of inferring additional mismatches not yet human-reviewed.
        value_mismatch = key in blocked_key_set
        eps_related = _is_eps(metric) or _is_eps(existing_metric_name)
        prior_stage_status = "blocked_apply_value_mismatch" if key in blocked_key_set else "queue_integrated_pending_human_review"
        if key in blocked_key_set and "value_mismatch" not in _norm(blocked_reason_map.get(key)):
            prior_stage_status = "blocked_apply_other_conflict"

        row = {
            "queue_item_id": queue_id,
            "suggestion_id": review_id,
            "source_pdf": source_pdf,
            "source_page": source_page,
            "source_row_reference": _norm(q.get("suggested_row_ids")),
            "statement_type": statement_type,
            "fiscal_year": year,
            "original_metric_name": original_metric_name,
            "suggested_metric_name": metric,
            "suggested_value": _norm(q.get("suggested_value")),
            "suggested_unit": _norm(q.get("suggested_unit")),
            "existing_metric_name": existing_metric_name,
            "existing_value": existing_value,
            "existing_unit": existing_unit,
            "conflict_type": conflict_type,
            "value_mismatch": _ensure_bool_str(value_mismatch),
            "duplicate_key": _ensure_bool_str(duplicate_key),
            "eps_related": _ensure_bool_str(eps_related),
            "ai_confidence": _norm(q.get("confidence")),
            "ai_rationale": _norm(q.get("reasoning_summary")),
            "prior_stage_status": prior_stage_status,
        }
        row["immutable_row_hash"] = _immutable_hash(row)

        # Human-fillable defaults.
        for f in HUMAN_FILLABLE_FIELDS:
            row[f] = ""
        row["schema_version"] = SCHEMA_VERSION
        row["second_review_required"] = "false"

        # Pre-mark blocked/value_mismatch as review-needed.
        if value_mismatch:
            row["human_decision"] = "REQUIRE_SECOND_REVIEW"
            row["decision_reason_code"] = "VALUE_MISMATCH_BLOCKED"
            row["reviewer_notes"] = "pre-marked by system: blocked value mismatch requires second review"
            row["needs_more_info_question"] = ""
            row["second_review_required"] = "true"
        template_rows.append(row)

    template_df = pd.DataFrame(template_rows)
    template_df.to_csv(OUT_TEMPLATE_CSV, index=False, encoding="utf-8-sig")
    with OUT_TEMPLATE_JSONL.open("w", encoding="utf-8") as f:
        for row in template_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    schema_payload = {
        "schema_version": SCHEMA_VERSION,
        "immutable_fields": IMMUTABLE_FIELDS + ["immutable_row_hash"],
        "human_fillable_fields": HUMAN_FILLABLE_FIELDS,
        "human_decision_enum": sorted(ALLOWED_DECISIONS),
        "forbidden_decisions": ["APPROVE_FOR_REAL_APPLY"],
        "forbidden_manual_fields": ["safe_to_apply", "real_apply", "write_production"],
        "notes": "safe_to_apply is derived downstream and never editable in human input",
    }
    _write_json(OUT_SCHEMA, schema_payload)

    validation_rules = {
        "schema_version_required": SCHEMA_VERSION,
        "required_fields": {
            "general": [
                "schema_version",
                "queue_item_id",
                "suggestion_id",
                "reviewer_id",
                "reviewer_role",
                "human_decision",
                "reviewer_notes",
                "reviewed_at_utc",
            ],
            "reject": ["decision_reason_code", "reviewer_notes"],
            "needs_more_info": ["needs_more_info_question", "reviewer_notes"],
            "require_second_review": ["second_review_required", "reviewer_notes"],
        },
        "enum": {"human_decision": sorted(ALLOWED_DECISIONS)},
        "immutable_validation": {
            "immutable_fields_must_not_change": IMMUTABLE_FIELDS,
            "immutable_row_hash_must_match": True,
        },
        "approve_rules": {
            "required_true_flags": [
                "evidence_checked",
                "source_row_confirmed",
                "fiscal_year_confirmed",
                "unit_confirmed",
                "value_confirmed",
            ],
            "forbid_when_value_mismatch": True,
            "forbid_when_true_value_conflict": True,
            "forbid_when_prior_stage_blocked": True,
            "forbid_when_corrected_fields_present": True,
        },
        "forced_rules": {
            "value_mismatch_or_true_value_conflict_requires": ["NEEDS_MORE_INFO", "REQUIRE_SECOND_REVIEW"],
        },
    }
    _write_json(OUT_VALIDATION_RULES, validation_rules)

    # Build a sample "real human input" example for validation run (not mock auto-approval).
    now_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    sample_rows: List[Dict[str, Any]] = []
    for row in template_rows:
        r = dict(row)
        r["reviewer_id"] = "analyst_001"
        r["reviewer_role"] = "finance_reviewer"
        r["reviewed_at_utc"] = now_utc
        # Blocked mismatch rows must not be approved.
        if _as_bool(r.get("value_mismatch")):
            r["human_decision"] = "REQUIRE_SECOND_REVIEW"
            r["decision_reason_code"] = "VALUE_MISMATCH_BLOCKED"
            r["reviewer_notes"] = "value mismatch vs existing preview, escalate to second review"
            r["second_review_required"] = "true"
            r["second_reviewer_id"] = "senior_reviewer_01"
            r["second_review_notes"] = "need source evidence compare"
            r["needs_more_info_question"] = ""
            r["evidence_checked"] = "true"
            r["source_row_confirmed"] = "false"
            r["fiscal_year_confirmed"] = "false"
            r["unit_confirmed"] = "true"
            r["value_confirmed"] = "false"
        else:
            # Keep non-blocked items conservative in this design stage.
            r["human_decision"] = "NEEDS_MORE_INFO"
            r["decision_reason_code"] = "EVIDENCE_GAP"
            r["reviewer_notes"] = "need additional source evidence before any sandbox preview approval"
            r["needs_more_info_question"] = "Please confirm metric-year-value mapping from source row."
            r["second_review_required"] = "false"
            r["evidence_checked"] = "true"
            r["source_row_confirmed"] = "false"
            r["fiscal_year_confirmed"] = "false"
            r["unit_confirmed"] = "true"
            r["value_confirmed"] = "false"
        sample_rows.append(r)

    sample_df = pd.DataFrame(sample_rows)
    sample_df.to_csv(OUT_SAMPLE_INPUT_CSV, index=False, encoding="utf-8-sig")

    # Validate sample input.
    original_map = {(row["queue_item_id"], row["suggestion_id"]): row for row in template_rows}
    seen = set()
    audit_rows: List[Dict[str, Any]] = []
    invalid_count = 0
    sandbox_preview_candidate_count = 0
    needs_more_info_count = 0
    require_second_review_count = 0
    blocked_value_mismatch_auto_apply_count = 0
    forced_count = 0

    for row in sample_rows:
        errs = _validate_row(row, original_map, seen)
        decision = _norm(row.get("human_decision"))
        mismatch = _as_bool(row.get("value_mismatch"))
        if decision == "APPROVE_FOR_SANDBOX_PREVIEW":
            sandbox_preview_candidate_count += 1
            if mismatch:
                blocked_value_mismatch_auto_apply_count += 1
        if decision == "NEEDS_MORE_INFO":
            needs_more_info_count += 1
        if decision == "REQUIRE_SECOND_REVIEW":
            require_second_review_count += 1
        if mismatch and decision in {"NEEDS_MORE_INFO", "REQUIRE_SECOND_REVIEW"}:
            forced_count += 1
        if errs:
            invalid_count += 1
        audit_rows.append(
            {
                "queue_item_id": row.get("queue_item_id", ""),
                "suggestion_id": row.get("suggestion_id", ""),
                "human_decision": decision,
                "value_mismatch": row.get("value_mismatch", ""),
                "row_valid": len(errs) == 0,
                "error_count": len(errs),
                "errors": "|".join(errs),
            }
        )

    pd.DataFrame(audit_rows).to_excel(OUT_VALIDATION_AUDIT, sheet_name="validation_audit", index=False, engine="openpyxl")

    # Candidate projection
    projection_rows = []
    for row in sample_rows:
        decision = _norm(row.get("human_decision"))
        mismatch = _as_bool(row.get("value_mismatch"))
        can_candidate = decision == "APPROVE_FOR_SANDBOX_PREVIEW" and not mismatch
        projection_rows.append(
            {
                "queue_item_id": row.get("queue_item_id", ""),
                "suggestion_id": row.get("suggestion_id", ""),
                "human_decision": decision,
                "value_mismatch": row.get("value_mismatch", ""),
                "sandbox_preview_candidate": can_candidate,
            }
        )
    pd.DataFrame(projection_rows).to_excel(OUT_CANDIDATE_PROJECTION, sheet_name="candidate_projection", index=False, engine="openpyxl")

    blocked_proof = {
        "blocked_value_mismatch_rows": [
            {
                "queue_item_id": r["queue_item_id"],
                "suggestion_id": r["suggestion_id"],
                "value_mismatch": r["value_mismatch"],
                "human_decision": r["human_decision"],
                "allowed_to_auto_apply": False,
            }
            for r in sample_rows
            if _as_bool(r.get("value_mismatch"))
        ],
        "blocked_value_mismatch_auto_apply_count": blocked_value_mismatch_auto_apply_count,
        "value_mismatch_forced_second_review_or_needs_more_info_count": forced_count,
    }
    _write_json(OUT_BLOCKED_PROOF, blocked_proof)

    after = _snapshot_hashes()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]
    delivery = _run_delivery_check()
    check_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "7T",
        "external_api_called": False,
        "real_apply_executed": False,
        "human_approval_template_generated": True,
        "approval_validation_rules_generated": True,
        "approval_input_schema_version": SCHEMA_VERSION,
        "real_human_input_supported": True,
        "mock_approval_required": False,
        "blocked_value_mismatch_auto_apply_count": blocked_value_mismatch_auto_apply_count,
        "value_mismatch_forced_second_review_or_needs_more_info_count": forced_count,
        "sandbox_preview_candidate_count": sandbox_preview_candidate_count,
        "needs_more_info_count": needs_more_info_count,
        "require_second_review_count": require_second_review_count,
        "invalid_approval_input_count": invalid_count,
        "ready_for_stage7u_real_human_approval_validation": bool(
            blocked_value_mismatch_auto_apply_count == 0
            and forced_count == len([r for r in sample_rows if _as_bool(r.get("value_mismatch"))])
            and invalid_count == 0
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
        "# Stage7T Real Human Approval Input Design",
        "",
        "No external API call; no real apply; no production write.",
        "",
        "## Design Outputs",
        f"- schema_version: {SCHEMA_VERSION}",
        f"- template_csv: {OUT_TEMPLATE_CSV.name}",
        f"- template_jsonl: {OUT_TEMPLATE_JSONL.name}",
        f"- validation_rules: {OUT_VALIDATION_RULES.name}",
        f"- sample_input: {OUT_SAMPLE_INPUT_CSV.name}",
        "",
        "## Safety Proof",
        f"- blocked_value_mismatch_auto_apply_count: {summary['blocked_value_mismatch_auto_apply_count']}",
        f"- value_mismatch_forced_second_review_or_needs_more_info_count: {summary['value_mismatch_forced_second_review_or_needs_more_info_count']}",
        "",
        "## Sample Validation",
        f"- sandbox_preview_candidate_count: {summary['sandbox_preview_candidate_count']}",
        f"- needs_more_info_count: {summary['needs_more_info_count']}",
        f"- require_second_review_count: {summary['require_second_review_count']}",
        f"- invalid_approval_input_count: {summary['invalid_approval_input_count']}",
        "",
        "## Guardrails",
        "- No APPROVE_FOR_REAL_APPLY decision exists.",
        "- No user-editable safe_to_apply field exists.",
        "- safe_to_apply remains downstream-derived only.",
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
        f"- ready_for_stage7u_real_human_approval_validation: {summary['ready_for_stage7u_real_human_approval_validation']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    # Explicit run output for user visibility.
    print(f"stage7t_external_api_called={str(summary['external_api_called']).lower()}")
    print(f"stage7t_real_apply_executed={str(summary['real_apply_executed']).lower()}")
    print(f"stage7t_schema_version={summary['approval_input_schema_version']}")
    print(f"stage7t_blocked_value_mismatch_auto_apply_count={summary['blocked_value_mismatch_auto_apply_count']}")
    print(
        "stage7t_value_mismatch_forced_second_review_or_needs_more_info_count="
        f"{summary['value_mismatch_forced_second_review_or_needs_more_info_count']}"
    )
    print(f"stage7t_invalid_approval_input_count={summary['invalid_approval_input_count']}")
    print(f"stage7t_check_delivery_state={summary['check_delivery_state_overall_status']}")
    print(f"stage7t_ready_for_stage7u={str(summary['ready_for_stage7u_real_human_approval_validation']).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
