import json
import re
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
IN_SUMMARY = BASE_DIR / "output" / "stage7o_five_case_new_model_batch_test" / "200_stage7o_five_case_summary.json"
IN_RAW = BASE_DIR / "output" / "stage7o_five_case_new_model_batch_test" / "200_stage7o_raw_responses_sanitized.jsonl"
IN_AUDIT = BASE_DIR / "output" / "stage7o_five_case_new_model_batch_test" / "200_stage7o_validation_audit.xlsx"
IN_REJECTED = BASE_DIR / "output" / "stage7o_five_case_new_model_batch_test" / "200_stage7o_rejected_suggestions.xlsx"
IN_SELECTED = BASE_DIR / "output" / "stage7o_five_case_new_model_batch_test" / "200_stage7o_selected_requests.jsonl"
IN_SCHEMA = BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_ai_review_response_schema.json"
IN_RULES = BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_ai_validation_rules.json"

OUT_DIR = BASE_DIR / "output" / "stage7o_fix_failure_analysis"
OUT_SUMMARY = OUT_DIR / "201_stage7o_fix_summary.json"
OUT_REPORT = OUT_DIR / "201_stage7o_fix_report.md"
OUT_FAILED_XLSX = OUT_DIR / "201_stage7o_failed_case_analysis.xlsx"
OUT_SCHEMA_POLICY = OUT_DIR / "201_stage7o_schema_repair_policy_draft.json"
OUT_RETRY_POLICY = OUT_DIR / "201_stage7o_retry_policy_draft.json"
OUT_RETRY_PLAN = OUT_DIR / "201_stage7o2_retry_plan.md"

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


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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
    required = [IN_SUMMARY, IN_RAW, IN_AUDIT, IN_REJECTED, IN_SELECTED, IN_SCHEMA, IN_RULES]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "stage7o_fix_failure_analysis",
                "mode": "analysis_only_no_api_call",
                "external_api_called": False,
                "blocked": True,
                "blocked_reason": f"missing_input:{'|'.join(missing)}",
            },
        )
        return 0

    before = _snapshot_hashes()

    summary = _load_json(IN_SUMMARY)
    raw_rows = _load_jsonl(IN_RAW)
    selected_rows = _load_jsonl(IN_SELECTED)
    audit_df = pd.read_excel(IN_AUDIT)
    rejected_df = pd.read_excel(IN_REJECTED)
    _schema = _load_json(IN_SCHEMA)
    _rules = _load_json(IN_RULES)

    selected_map = {_norm(r.get("review_id")): r for r in selected_rows}

    http_503_rows = [r for r in raw_rows if int(r.get("http_status") or 0) == 503]
    schema_invalid_rows = [r for r in raw_rows if _norm(r.get("error_type")) == "schema_invalid"]

    schema_invalid_missing_required_fields: List[str] = []
    schema_invalid_type_error_fields: List[str] = []
    schema_repairable_case_count = 0

    failed_case_rows: List[Dict[str, Any]] = []
    for r in raw_rows:
        review_id = _norm(r.get("review_id"))
        rid_df = audit_df[audit_df["review_id"] == review_id]
        schema_errors_text = ""
        logic_errors_text = ""
        missing_fields_text = ""
        hallucinated_count = 0
        invalid_ref_count = 0
        bad_eps_count = 0
        requires_human = False
        if not rid_df.empty:
            rec = rid_df.iloc[0]
            schema_errors_text = _norm(rec.get("schema_errors"))
            logic_errors_text = _norm(rec.get("logic_errors"))
            missing_fields_text = _norm(rec.get("missing_required_fields"))
            hallucinated_count = int(rec.get("hallucinated_value_count") or 0)
            invalid_ref_count = int(rec.get("invalid_source_row_reference_count") or 0)
            bad_eps_count = int(rec.get("bad_eps_ratio_count") or 0)
            requires_human = bool(rec.get("requires_human_approval"))

        is_failed = bool(not r.get("response_json_parse_success") or _norm(r.get("error_type")) in {"connection_error", "schema_invalid"})
        if not is_failed:
            continue

        failure_kind = "other"
        if int(r.get("http_status") or 0) == 503:
            failure_kind = "http_503"
        elif _norm(r.get("error_type")) == "schema_invalid":
            failure_kind = "schema_invalid"
        elif _norm(r.get("error_type")) == "connection_error":
            failure_kind = "connection_error"

        type_error_fields = re.findall(r"type_mismatch:([^:|]+):", schema_errors_text + "|" + logic_errors_text)
        missing_fields = [x for x in _norm(missing_fields_text).split("|") if x]
        if failure_kind == "schema_invalid":
            for m in missing_fields:
                if m not in schema_invalid_missing_required_fields:
                    schema_invalid_missing_required_fields.append(m)
            for t in type_error_fields:
                if t not in schema_invalid_type_error_fields:
                    schema_invalid_type_error_fields.append(t)

        # Repairability rules for this round:
        # allowed repair: confidence str->float, suggested_row_ids str->array, risk_flags str->array,
        # requires_human_approval str->bool then force true, null->"" for suggested_value/unit only.
        # NOT allowed for suggested_metric_name null/type mismatch.
        repairable = False
        if failure_kind == "schema_invalid":
            if type_error_fields:
                safe_type_fields = {"confidence", "suggested_row_ids", "risk_flags", "requires_human_approval", "suggested_value", "suggested_unit"}
                if set(type_error_fields).issubset(safe_type_fields):
                    repairable = True
            if missing_fields:
                repairable = False
            if repairable:
                schema_repairable_case_count += 1

        req = selected_map.get(review_id, {})
        failed_case_rows.append(
            {
                "review_id": review_id,
                "request_index": r.get("request_index"),
                "failure_kind": failure_kind,
                "http_status": r.get("http_status"),
                "error_type": _norm(r.get("error_type")),
                "error_summary": _norm(r.get("error_summary")),
                "manual_review_reason": _norm(req.get("manual_review_reason")),
                "metric": _norm(req.get("candidate_rows", [{}])[0].get("normalized_metric_name")) if req.get("candidate_rows") else "",
                "candidate_rows_count": len(req.get("candidate_rows", [])),
                "schema_errors": schema_errors_text,
                "logic_errors": logic_errors_text,
                "missing_required_fields": "|".join(missing_fields),
                "type_error_fields": "|".join(type_error_fields),
                "hallucinated_value_count": hallucinated_count,
                "invalid_source_row_reference_count": invalid_ref_count,
                "bad_eps_ratio_count": bad_eps_count,
                "requires_human_approval": requires_human,
                "schema_repairable_under_policy": repairable,
            }
        )

    pd.DataFrame(failed_case_rows).to_excel(OUT_FAILED_XLSX, index=False, engine="openpyxl")

    schema_repair_policy = {
        "stage": "stage7o_fix_failure_analysis",
        "policy_name": "stage7o_safe_schema_repair_policy_draft",
        "safe_repairs_allowed": [
            "confidence: numeric-string -> float",
            "suggested_row_ids: single string -> string array",
            "risk_flags: single string -> string array",
            "requires_human_approval: 'true'/'false' string -> boolean, then force true",
            "suggested_value: null -> ''",
            "suggested_unit: null -> ''",
        ],
        "safe_repairs_forbidden": [
            "fabricate suggested_value",
            "fabricate suggested_row_ids",
            "reference non-existent row_id",
            "auto-accept true_value_conflict into clean preview",
            "EPS mapped to ratio",
            "modify source candidate raw values",
            "modify production files",
            "auto-repair suggested_metric_name null/type mismatch without evidence",
        ],
        "current_failed_schema_cases": [r["review_id"] for r in failed_case_rows if r["failure_kind"] == "schema_invalid"],
        "current_schema_repairable_case_count": schema_repairable_case_count,
    }
    _write_json(OUT_SCHEMA_POLICY, schema_repair_policy)

    retry_policy = {
        "stage": "stage7o_fix_failure_analysis",
        "policy_name": "stage7o_retry_policy_draft",
        "retry_rules": {
            "http_503": {"allow_retry": True, "max_retry": 1, "interval_seconds": 10, "scope": "failed_cases_only"},
            "http_429": {"allow_retry": False, "action": "stop_sample_expansion_immediately"},
            "timeout": {"allow_retry": False, "action": "route_to_later_retry_queue_or_manual_review"},
            "schema_invalid": {"allow_retry": True, "max_retry": 1, "pre_step": "safe_schema_repair_attempt"},
        },
        "post_retry_guards": [
            "all suggestions must keep requires_human_approval=true",
            "deterministic validation must pass",
            "no production write-back",
        ],
        "recommended_scope": "failed_cases_only",
        "failed_case_review_ids": [r["review_id"] for r in failed_case_rows],
    }
    _write_json(OUT_RETRY_POLICY, retry_policy)

    retry_plan_md = "\n".join(
        [
            "# Stage7O2 Retry Plan",
            "",
            "1. Retry scope: failed cases only (`stage7i_review_0001`, `stage7i_review_0013`).",
            "2. For HTTP 503 case: one retry allowed after 10 seconds.",
            "3. For schema_invalid case: run safe schema repair pre-check; if not repairable, re-request once with stricter field-type constraint.",
            "4. Keep `requires_human_approval=true` for all outputs.",
            "5. Keep sandbox-only mode; do not write to production 06.",
            "6. Stop expansion immediately on any HTTP 429.",
            "7. Keep timeout and max_tokens unchanged unless retry still fails.",
        ]
    )
    _write_md(OUT_RETRY_PLAN, retry_plan_md)

    hallucinated_value_count = int(audit_df["hallucinated_value_count"].fillna(0).sum())
    invalid_source_row_reference_count = int(audit_df["invalid_source_row_reference_count"].fillna(0).sum())
    bad_eps_ratio_count = int(audit_df["bad_eps_ratio_count"].fillna(0).sum())

    after = _snapshot_hashes()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]
    delivery = _run_delivery_check()
    check_status = _norm(delivery.get("overall_status"))

    fix_summary = {
        "stage": "stage7o_fix_failure_analysis",
        "mode": "analysis_only_no_api_call",
        "based_on_stage7o_commit": "c540c4c11081f66cdedd355ce578781a711c009a",
        "external_api_called": False,
        "stage7o_selected_review_request_count": int(summary.get("selected_review_request_count", 0)),
        "stage7o_validated_suggestion_count": int(summary.get("validated_suggestion_count", 0)),
        "stage7o_rejected_suggestion_count": int(summary.get("rejected_suggestion_count", 0)),
        "http_503_case_count": len(http_503_rows),
        "schema_invalid_case_count": len(schema_invalid_rows),
        "schema_invalid_missing_required_fields": schema_invalid_missing_required_fields,
        "schema_invalid_type_error_fields": schema_invalid_type_error_fields,
        "schema_repairable_case_count": schema_repairable_case_count,
        "schema_repair_policy_generated": True,
        "retry_policy_generated": True,
        "hallucinated_value_count": hallucinated_value_count,
        "invalid_source_row_reference_count": invalid_source_row_reference_count,
        "bad_eps_ratio_count": bad_eps_ratio_count,
        "recommended_stage7o2_retry_scope": "failed_cases_only",
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": check_status,
        "ready_for_stage7o2_failed_case_retry": True,
    }
    _write_json(OUT_SUMMARY, fix_summary)

    report_md = "\n".join(
        [
            "# Stage7O-Fix Failure Analysis",
            "",
            "## Findings",
            f"- HTTP 503 case count: {fix_summary['http_503_case_count']}",
            f"- Schema invalid case count: {fix_summary['schema_invalid_case_count']}",
            f"- Schema invalid missing required fields: {fix_summary['schema_invalid_missing_required_fields']}",
            f"- Schema invalid type error fields: {fix_summary['schema_invalid_type_error_fields']}",
            f"- Schema repairable case count: {fix_summary['schema_repairable_case_count']}",
            "",
            "## Failed Cases",
            "- `stage7i_review_0001`: HTTP 503 (service-side transient failure).",
            "- `stage7i_review_0013`: schema invalid due to `suggested_metric_name` type mismatch (null where string required).",
            "",
            "## Safety Checks",
            f"- hallucinated_value_count: {fix_summary['hallucinated_value_count']}",
            f"- invalid_source_row_reference_count: {fix_summary['invalid_source_row_reference_count']}",
            f"- bad_eps_ratio_count: {fix_summary['bad_eps_ratio_count']}",
            "",
            "## Next Step",
            "- Retry scope: failed cases only.",
            "- Apply retry + safe repair policy drafts in Stage7O2.",
            "",
            f"- check_delivery_state_overall_status: {fix_summary['check_delivery_state_overall_status']}",
        ]
    )
    _write_md(OUT_REPORT, report_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
