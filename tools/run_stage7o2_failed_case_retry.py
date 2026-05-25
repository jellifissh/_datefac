import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

import pandas as pd
import requests

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

BASE_DIR = Path(r"D:\_datefac")

IN_STAGE7O_SUMMARY = BASE_DIR / "output" / "stage7o_five_case_new_model_batch_test" / "200_stage7o_five_case_summary.json"
IN_STAGE7O_SELECTED = BASE_DIR / "output" / "stage7o_five_case_new_model_batch_test" / "200_stage7o_selected_requests.jsonl"
IN_STAGE7O_RAW = BASE_DIR / "output" / "stage7o_five_case_new_model_batch_test" / "200_stage7o_raw_responses_sanitized.jsonl"
IN_STAGE7O_AUDIT = BASE_DIR / "output" / "stage7o_five_case_new_model_batch_test" / "200_stage7o_validation_audit.xlsx"
IN_STAGE7O_REJ = BASE_DIR / "output" / "stage7o_five_case_new_model_batch_test" / "200_stage7o_rejected_suggestions.xlsx"
IN_STAGE7O_FIX_SUMMARY = BASE_DIR / "output" / "stage7o_fix_failure_analysis" / "201_stage7o_fix_summary.json"
IN_STAGE7O_FIX_FAILED = BASE_DIR / "output" / "stage7o_fix_failure_analysis" / "201_stage7o_failed_case_analysis.xlsx"
IN_RETRY_POLICY = BASE_DIR / "output" / "stage7o_fix_failure_analysis" / "201_stage7o_retry_policy_draft.json"
IN_SCHEMA_REPAIR_POLICY = BASE_DIR / "output" / "stage7o_fix_failure_analysis" / "201_stage7o_schema_repair_policy_draft.json"
IN_SCHEMA = BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_ai_review_response_schema.json"
IN_RULES = BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_ai_validation_rules.json"

OUT_DIR = BASE_DIR / "output" / "stage7o2_failed_case_retry"
OUT_SUMMARY = OUT_DIR / "202_stage7o2_failed_case_retry_summary.json"
OUT_REPORT = OUT_DIR / "202_stage7o2_failed_case_retry_report.md"
OUT_SELECTED = OUT_DIR / "202_stage7o2_retry_selected_requests.jsonl"
OUT_RAW = OUT_DIR / "202_stage7o2_raw_responses_sanitized.jsonl"
OUT_AUDIT = OUT_DIR / "202_stage7o2_validation_audit.xlsx"
OUT_VALID = OUT_DIR / "202_stage7o2_validated_suggestions.xlsx"
OUT_REJ = OUT_DIR / "202_stage7o2_rejected_suggestions.xlsx"
OUT_RETRY_RESULT = OUT_DIR / "202_stage7o2_retry_result.json"

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


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_excel(path: Path, sheet: str, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_excel(path, sheet_name=sheet[:31], index=False, engine="openpyxl")


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


def _sanitize_base_url(base_url: str) -> str:
    if not _norm(base_url):
        return ""
    parsed = urlparse(base_url)
    scheme = parsed.scheme or "https"
    host = parsed.hostname or ""
    path = parsed.path or ""
    return f"{scheme}://{host}{path}"


def _is_eps_case(req: Dict[str, Any]) -> bool:
    for r in req.get("candidate_rows", []):
        text = (_norm(r.get("normalized_metric_name")) + " " + _norm(r.get("raw_metric_name"))).lower()
        if "eps" in text or "姣忚偂鏀剁泭" in text:
            return True
    return False


def _extract_failed_ids(raw_rows: List[Dict[str, Any]]) -> Tuple[str, str]:
    http_503_id = ""
    schema_invalid_id = ""
    for r in raw_rows:
        if int(r.get("http_status") or 0) == 503 and not http_503_id:
            http_503_id = _norm(r.get("review_id"))
        if _norm(r.get("error_type")) == "schema_invalid" and not schema_invalid_id:
            schema_invalid_id = _norm(r.get("review_id"))
    return http_503_id, schema_invalid_id


def _build_prompt(req: Dict[str, Any], required_fields: List[str]) -> str:
    compact_rows = []
    for row in req.get("candidate_rows", []):
        compact_rows.append(
            {
                "row_id": _norm(row.get("row_id")),
                "statement_type": _norm(row.get("statement_type")),
                "normalized_metric_name": _norm(row.get("normalized_metric_name")),
                "raw_metric_name": _norm(row.get("raw_metric_name")),
                "year": _norm(row.get("year")),
                "value": _norm(row.get("value")),
                "unit": _norm(row.get("unit")),
                "source_page": _norm(row.get("source_page")),
                "source_text_excerpt": _norm(row.get("source_text_excerpt"))[:120],
            }
        )

    payload = {
        "review_id": _norm(req.get("review_id")),
        "manual_review_reason": _norm(req.get("manual_review_reason")),
        "candidate_rows": compact_rows,
        "known_rules": {
            "eps_do_not_use_ratio": True,
            "value_must_come_from_candidate_rows": True,
            "requires_human_approval_must_be_true": True,
        },
    }

    return (
        "Only output ONE JSON object. No Markdown. No explanation text outside JSON.\n"
        "All fields must exist even when empty. Required fields: "
        + ", ".join(required_fields)
        + ".\n"
        "Type constraints:\n"
        "- review_id: string\n"
        "- suggested_action: string(enum)\n"
        "- suggested_row_ids: array\n"
        "- suggested_metric_name: string\n"
        "- suggested_year: string\n"
        "- suggested_value: string\n"
        "- suggested_unit: string\n"
        "- confidence: number between 0 and 1\n"
        "- reasoning_summary: string\n"
        "- risk_flags: array\n"
        "- requires_human_approval: boolean and must be true\n"
        "Safety constraints:\n"
        "- suggested_row_ids must be from candidate_rows.row_id\n"
        "- suggested_value must come from candidate_rows.value; if uncertain, use empty string\n"
        "- suggested_unit must come from candidate_rows.unit or empty string\n"
        "- If uncertain, suggested_action must be keep_manual_review\n"
        "- EPS must not be ratio\n"
        "Return this exact shape:\n"
        "{"
        "\"review_id\":\"\","
        "\"suggested_action\":\"accept_one / merge_same_value / split_metric / exclude / keep_manual_review\","
        "\"suggested_row_ids\":[],"
        "\"suggested_metric_name\":\"\","
        "\"suggested_year\":\"\","
        "\"suggested_value\":\"\","
        "\"suggested_unit\":\"\","
        "\"confidence\":0.0,"
        "\"reasoning_summary\":\"\","
        "\"risk_flags\":[],"
        "\"requires_human_approval\":true"
        "}\n"
        "Input:\n"
        + json.dumps(payload, ensure_ascii=False)
    )


def _parse_json_content(text: str) -> Tuple[Dict[str, Any], str]:
    t = _norm(text)
    if not t:
        raise ValueError("empty_response")
    try:
        return json.loads(t), "raw_json"
    except Exception:
        pass
    if "```" in t:
        for seg in t.split("```"):
            s = seg.strip()
            if s.startswith("json"):
                s = s[4:].strip()
            if s.startswith("{") and s.endswith("}"):
                return json.loads(s), "fence_repair"
    l = t.find("{")
    r = t.rfind("}")
    if l >= 0 and r > l:
        return json.loads(t[l : r + 1]), "slice_repair"
    raise ValueError("json_parse_failed")


def _schema_validate(resp: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    missing: List[str] = []
    required = schema.get("required", [])
    props = schema.get("properties", {})

    for k in required:
        if k not in resp:
            missing.append(k)
            errors.append(f"missing_required:{k}")

    tmap = {"string": str, "number": (int, float), "array": list, "boolean": bool}
    for k, spec in props.items():
        if k not in resp:
            continue
        et = spec.get("type")
        if et in tmap and not isinstance(resp[k], tmap[et]):
            errors.append(f"type_mismatch:{k}:{et}")

    # Stronger mandatory checks for this stage
    if "suggested_metric_name" in resp and not isinstance(resp.get("suggested_metric_name"), str):
        errors.append("type_mismatch:suggested_metric_name:string")
    if "suggested_year" in resp and not isinstance(resp.get("suggested_year"), str):
        errors.append("type_mismatch:suggested_year:string")
    if "suggested_value" in resp and not isinstance(resp.get("suggested_value"), str):
        errors.append("type_mismatch:suggested_value:string")
    if "suggested_unit" in resp and not isinstance(resp.get("suggested_unit"), str):
        errors.append("type_mismatch:suggested_unit:string")
    if "suggested_row_ids" in resp and not isinstance(resp.get("suggested_row_ids"), list):
        errors.append("type_mismatch:suggested_row_ids:array")
    if "risk_flags" in resp and not isinstance(resp.get("risk_flags"), list):
        errors.append("type_mismatch:risk_flags:array")
    if "requires_human_approval" in resp and not isinstance(resp.get("requires_human_approval"), bool):
        errors.append("type_mismatch:requires_human_approval:boolean")
    if "confidence" in resp and not isinstance(resp.get("confidence"), (int, float)):
        errors.append("type_mismatch:confidence:number")

    enum_vals = props.get("suggested_action", {}).get("enum", [])
    if enum_vals and _norm(resp.get("suggested_action")) not in set(enum_vals):
        errors.append("suggested_action_enum_invalid")

    try:
        c = float(resp.get("confidence"))
        if c < 0 or c > 1:
            errors.append("confidence_out_of_range")
    except Exception:
        errors.append("confidence_not_numeric")

    if resp.get("requires_human_approval") is not True:
        errors.append("requires_human_approval_must_be_true")

    return sorted(set(errors)), missing


def _logic_validate(req: Dict[str, Any], resp: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    hallucinated = 0
    invalid_ref = 0
    bad_eps = 0

    row_map = {_norm(r.get("row_id")): r for r in req.get("candidate_rows", [])}
    candidate_values = {_norm(r.get("value")) for r in req.get("candidate_rows", [])}
    candidate_units = {_norm(r.get("unit")) for r in req.get("candidate_rows", [])}
    selected_ids = resp.get("suggested_row_ids", [])
    if not isinstance(selected_ids, list):
        selected_ids = []
    selected_ids = [_norm(x) for x in selected_ids]

    for rid in selected_ids:
        if rid not in row_map:
            invalid_ref += 1
            errors.append("invalid_source_row_reference")
            break

    suggested_value = _norm(resp.get("suggested_value"))
    if suggested_value and suggested_value not in candidate_values:
        hallucinated += 1
        errors.append("hallucinated_value")

    suggested_unit = _norm(resp.get("suggested_unit"))
    if suggested_unit and suggested_unit not in candidate_units:
        errors.append("invalid_suggested_unit")

    # EPS should never be ratio
    is_eps = _is_eps_case(req)
    if is_eps:
        unit_text = suggested_unit.lower()
        if "%" in unit_text or "ratio" in unit_text:
            bad_eps += 1
            errors.append("eps_ratio_error")

    try:
        c = float(resp.get("confidence"))
        if c < 0 or c > 1:
            errors.append("confidence_out_of_range")
    except Exception:
        errors.append("confidence_not_numeric")

    if resp.get("requires_human_approval") is not True:
        errors.append("requires_human_approval_must_be_true")

    return {
        "errors": sorted(set(errors)),
        "validation_pass": len(errors) == 0,
        "hallucinated_value_count": hallucinated,
        "invalid_source_row_reference_count": invalid_ref,
        "bad_eps_ratio_count": bad_eps,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    required = [
        IN_STAGE7O_SUMMARY,
        IN_STAGE7O_SELECTED,
        IN_STAGE7O_RAW,
        IN_STAGE7O_AUDIT,
        IN_STAGE7O_REJ,
        IN_STAGE7O_FIX_SUMMARY,
        IN_STAGE7O_FIX_FAILED,
        IN_RETRY_POLICY,
        IN_SCHEMA_REPAIR_POLICY,
        IN_SCHEMA,
        IN_RULES,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "stage7o2_failed_case_retry",
                "mode": "real_api_failed_cases_only_retry",
                "external_api_called": False,
                "blocked": True,
                "blocked_reason": f"missing_input:{'|'.join(missing)}",
            },
        )
        return 0

    before = _snapshot_hashes()

    stage7o_summary = _load_json(IN_STAGE7O_SUMMARY)
    selected_rows = _load_jsonl(IN_STAGE7O_SELECTED)
    raw_rows = _load_jsonl(IN_STAGE7O_RAW)
    _ = pd.read_excel(IN_STAGE7O_AUDIT)
    _ = pd.read_excel(IN_STAGE7O_REJ)
    _ = _load_json(IN_STAGE7O_FIX_SUMMARY)
    _ = pd.read_excel(IN_STAGE7O_FIX_FAILED)
    retry_policy = _load_json(IN_RETRY_POLICY)
    _ = _load_json(IN_SCHEMA_REPAIR_POLICY)
    schema = _load_json(IN_SCHEMA)
    _ = _load_json(IN_RULES)

    http_503_id, schema_invalid_id = _extract_failed_ids(raw_rows)
    selected_map = {_norm(x.get("review_id")): x for x in selected_rows}
    retry_targets: List[Dict[str, Any]] = []
    for rid in [http_503_id, schema_invalid_id]:
        if rid and rid in selected_map:
            retry_targets.append(selected_map[rid])

    # Fallback: enforce exactly first two failed rows if IDs are incomplete.
    if len(retry_targets) < 2:
        fallback_ids: List[str] = []
        for r in raw_rows:
            failed = int(r.get("http_status") or 0) >= 400 or _norm(r.get("error_type")) in {"schema_invalid", "timeout", "connection_error"}
            if failed:
                rid = _norm(r.get("review_id"))
                if rid and rid not in fallback_ids:
                    fallback_ids.append(rid)
            if len(fallback_ids) >= 2:
                break
        retry_targets = [selected_map[rid] for rid in fallback_ids if rid in selected_map][:2]

    _write_jsonl(OUT_SELECTED, retry_targets)

    api_key = os.environ.get("AI_REVIEW_API_KEY", "")
    base_url = _norm(os.environ.get("AI_REVIEW_BASE_URL", ""))
    model = _norm(os.environ.get("AI_REVIEW_MODEL", ""))
    api_key_present = bool(api_key)
    base_url_present = bool(base_url)
    model_present = bool(model)
    base_url_sanitized = _sanitize_base_url(base_url)

    external_api_called = False
    timeout_seconds = 90
    max_tokens = 700
    temperature = 0

    raw_out: List[Dict[str, Any]] = []
    audits: List[Dict[str, Any]] = []
    validated_rows: List[Dict[str, Any]] = []
    rejected_rows: List[Dict[str, Any]] = []
    retry_results: List[Dict[str, Any]] = []
    latencies: List[float] = []
    type_error_fields_after_retry: List[str] = []

    rate_limited_count = 0
    timeout_count = 0
    http_503_count_after_retry = 0
    missing_required_fields_total: List[str] = []

    if api_key_present and base_url_present and model_present and retry_targets:
        external_api_called = True
        endpoint = base_url.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        required_fields = schema.get("required", [])

        for idx, req in enumerate(retry_targets):
            review_id = _norm(req.get("review_id"))
            mode = "http_503_retry" if review_id == http_503_id else "schema_invalid_retry"
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "Return only one strict JSON object."},
                    {"role": "user", "content": _build_prompt(req, required_fields)},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            }

            http_status = None
            timed_out = False
            rate_limited = False
            error_type = ""
            error_summary = ""
            parse_method = ""
            response_json_parse_success = False
            parsed_obj: Dict[str, Any] = {}
            usage: Dict[str, Any] = {}
            schema_errors: List[str] = []
            missing_fields: List[str] = []
            logic = {
                "errors": ["response_not_available"],
                "validation_pass": False,
                "hallucinated_value_count": 0,
                "invalid_source_row_reference_count": 0,
                "bad_eps_ratio_count": 0,
            }

            t0 = time.time()
            try:
                resp = requests.post(endpoint, headers=headers, json=payload, timeout=timeout_seconds)
                elapsed = round(time.time() - t0, 3)
                latencies.append(elapsed)
                http_status = resp.status_code

                if resp.status_code == 503:
                    http_503_count_after_retry += 1
                    error_type = "connection_error"
                    error_summary = "HTTP 503"
                elif resp.status_code == 429:
                    rate_limited = True
                    rate_limited_count += 1
                    error_type = "rate_limit"
                    error_summary = "HTTP 429"
                elif resp.status_code >= 400:
                    error_type = "connection_error"
                    error_summary = f"HTTP {resp.status_code}"
                else:
                    data = resp.json()
                    usage = data.get("usage", {}) if isinstance(data, dict) else {}
                    content = ""
                    if isinstance(data, dict):
                        choices = data.get("choices", [])
                        if choices:
                            content = _norm(choices[0].get("message", {}).get("content"))
                    parsed_obj, parse_method = _parse_json_content(content)
                    response_json_parse_success = True
                    schema_errors, missing_fields = _schema_validate(parsed_obj, schema)
                    for m in missing_fields:
                        if m not in missing_required_fields_total:
                            missing_required_fields_total.append(m)
                    for e in schema_errors:
                        if e.startswith("type_mismatch:"):
                            field = e.split(":")[1]
                            if field not in type_error_fields_after_retry:
                                type_error_fields_after_retry.append(field)
                    if not schema_errors:
                        logic = _logic_validate(req, parsed_obj)
                    else:
                        logic = {
                            "errors": schema_errors,
                            "validation_pass": False,
                            "hallucinated_value_count": 0,
                            "invalid_source_row_reference_count": 0,
                            "bad_eps_ratio_count": 0,
                        }
                        error_type = "schema_invalid"
                        error_summary = "schema validation failed"
            except requests.exceptions.Timeout:
                elapsed = round(time.time() - t0, 3)
                latencies.append(elapsed)
                timed_out = True
                timeout_count += 1
                error_type = "timeout"
                error_summary = "request timeout"
            except Exception as e:
                elapsed = round(time.time() - t0, 3)
                latencies.append(elapsed)
                error_type = "connection_error"
                error_summary = f"{e.__class__.__name__}:{_norm(e)}"

            raw_out.append(
                {
                    "review_id": review_id,
                    "retry_mode": mode,
                    "request_index": idx + 1,
                    "http_status": http_status,
                    "rate_limited": rate_limited,
                    "timeout": timed_out,
                    "parse_method": parse_method,
                    "response_json_parse_success": response_json_parse_success,
                    "error_type": error_type,
                    "error_summary": error_summary,
                    "usage": usage,
                    "response_obj": parsed_obj if response_json_parse_success else {},
                }
            )

            schema_valid = bool(response_json_parse_success and not schema_errors)
            logic_valid = bool(logic.get("validation_pass", False))
            validation_pass = schema_valid and logic_valid
            audits.append(
                {
                    "review_id": review_id,
                    "retry_mode": mode,
                    "schema_valid": schema_valid,
                    "logic_valid": logic_valid,
                    "validation_pass": validation_pass,
                    "schema_errors": "|".join(schema_errors),
                    "logic_errors": "|".join(logic.get("errors", [])),
                    "missing_required_fields": "|".join(missing_fields),
                    "hallucinated_value_count": int(logic.get("hallucinated_value_count", 0) or 0),
                    "invalid_source_row_reference_count": int(logic.get("invalid_source_row_reference_count", 0) or 0),
                    "bad_eps_ratio_count": int(logic.get("bad_eps_ratio_count", 0) or 0),
                    "requires_human_approval": bool(parsed_obj.get("requires_human_approval", False)) if response_json_parse_success else False,
                }
            )

            if validation_pass:
                validated_rows.append(
                    {
                        "review_id": review_id,
                        "suggested_action": _norm(parsed_obj.get("suggested_action")),
                        "suggested_row_ids": "|".join(parsed_obj.get("suggested_row_ids", [])),
                        "suggested_metric_name": _norm(parsed_obj.get("suggested_metric_name")),
                        "suggested_year": _norm(parsed_obj.get("suggested_year")),
                        "suggested_value": _norm(parsed_obj.get("suggested_value")),
                        "suggested_unit": _norm(parsed_obj.get("suggested_unit")),
                        "confidence": parsed_obj.get("confidence", ""),
                        "reasoning_summary": _norm(parsed_obj.get("reasoning_summary")),
                        "risk_flags": "|".join(parsed_obj.get("risk_flags", [])),
                        "requires_human_approval": bool(parsed_obj.get("requires_human_approval", False)),
                    }
                )
            else:
                rejected_rows.append(
                    {
                        "review_id": review_id,
                        "retry_mode": mode,
                        "error_type": error_type or "validation_failed",
                        "error_summary": error_summary,
                        "schema_errors": "|".join(schema_errors),
                        "logic_errors": "|".join(logic.get("errors", [])),
                    }
                )

            retry_results.append(
                {
                    "review_id": review_id,
                    "retry_mode": mode,
                    "http_status": http_status,
                    "response_json_parse_success": response_json_parse_success,
                    "validation_pass": validation_pass,
                    "error_type": error_type,
                    "error_summary": error_summary,
                }
            )

            if idx < len(retry_targets) - 1:
                time.sleep(10)

    _write_jsonl(OUT_RAW, raw_out)
    _write_excel(OUT_AUDIT, "validation_audit", audits)
    _write_excel(OUT_VALID, "validated_suggestions", validated_rows)
    _write_excel(OUT_REJ, "rejected_suggestions", rejected_rows)
    _write_json(OUT_RETRY_RESULT, {"retry_policy": retry_policy, "results": retry_results})

    real_api_response_count = int(sum(1 for r in raw_out if r.get("response_json_parse_success")))
    schema_valid_response_count = int(sum(1 for a in audits if a.get("schema_valid")))
    schema_invalid_response_count = int(sum(1 for a in audits if not a.get("schema_valid")))
    validated_suggestion_count = int(len(validated_rows))
    rejected_suggestion_count = int(len(rejected_rows))
    requires_human_approval_count = int(sum(1 for a in audits if a.get("requires_human_approval")))
    hallucinated_value_count = int(sum(int(a.get("hallucinated_value_count", 0) or 0) for a in audits))
    invalid_source_row_reference_count = int(sum(int(a.get("invalid_source_row_reference_count", 0) or 0) for a in audits))
    bad_eps_ratio_count = int(sum(int(a.get("bad_eps_ratio_count", 0) or 0) for a in audits))

    after = _snapshot_hashes()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]
    delivery = _run_delivery_check()
    check_status = _norm(delivery.get("overall_status"))

    http_503_retry_attempted = bool(http_503_id and any(_norm(x.get("review_id")) == http_503_id for x in retry_targets))
    schema_invalid_retry_attempted = bool(schema_invalid_id and any(_norm(x.get("review_id")) == schema_invalid_id for x in retry_targets))

    ready_for_stage7p = bool(
        len(retry_targets) == 2
        and real_api_response_count == 2
        and schema_valid_response_count == 2
        and schema_invalid_response_count == 0
        and validated_suggestion_count == 2
        and rejected_suggestion_count == 0
        and rate_limited_count == 0
        and timeout_count == 0
        and http_503_count_after_retry == 0
        and len(type_error_fields_after_retry) == 0
        and hallucinated_value_count == 0
        and invalid_source_row_reference_count == 0
        and bad_eps_ratio_count == 0
        and requires_human_approval_count == 2
    )

    summary = {
        "stage": "stage7o2_failed_case_retry",
        "mode": "real_api_failed_cases_only_retry",
        "based_on_stage7o_fix_commit": "5757253ac01b4ff9a92aca9153a4df8164abaaf8",
        "external_api_called": external_api_called,
        "model": model,
        "base_url_sanitized": base_url_sanitized,
        "api_key_present": api_key_present,
        "api_key_committed": False,
        "api_key_logged": False,
        "failed_case_retry_count": len(retry_targets),
        "http_503_retry_attempted": http_503_retry_attempted,
        "schema_invalid_retry_attempted": schema_invalid_retry_attempted,
        "real_api_response_count": real_api_response_count,
        "schema_valid_response_count": schema_valid_response_count,
        "schema_invalid_response_count": schema_invalid_response_count,
        "validated_suggestion_count": validated_suggestion_count,
        "rejected_suggestion_count": rejected_suggestion_count,
        "rate_limited_count": rate_limited_count,
        "timeout_count": timeout_count,
        "http_503_count_after_retry": http_503_count_after_retry,
        "schema_type_error_fields_after_retry": sorted(type_error_fields_after_retry),
        "missing_required_fields_total": missing_required_fields_total,
        "hallucinated_value_count": hallucinated_value_count,
        "invalid_source_row_reference_count": invalid_source_row_reference_count,
        "bad_eps_ratio_count": bad_eps_ratio_count,
        "requires_human_approval_count": requires_human_approval_count,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": check_status,
        "ready_for_stage7p_ai_suggestion_queue_integration": ready_for_stage7p,
        "source_stage7o_selected_review_request_count": int(stage7o_summary.get("selected_review_request_count", 0)),
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# Stage7O2 Failed-case Retry",
        "",
        "## Scope",
        f"- failed_case_retry_count: {summary['failed_case_retry_count']}",
        f"- http_503_retry_attempted: {summary['http_503_retry_attempted']}",
        f"- schema_invalid_retry_attempted: {summary['schema_invalid_retry_attempted']}",
        "- request_interval_seconds: 10",
        "- timeout_seconds: 90",
        "- max_tokens: 700",
        "- temperature: 0",
        "",
        "## Result",
        f"- real_api_response_count: {summary['real_api_response_count']}",
        f"- schema_valid/invalid: {summary['schema_valid_response_count']}/{summary['schema_invalid_response_count']}",
        f"- validated/rejected: {summary['validated_suggestion_count']}/{summary['rejected_suggestion_count']}",
        f"- rate_limited_count/timeout_count: {summary['rate_limited_count']}/{summary['timeout_count']}",
        f"- http_503_count_after_retry: {summary['http_503_count_after_retry']}",
        f"- schema_type_error_fields_after_retry: {summary['schema_type_error_fields_after_retry']}",
        f"- hallucinated_value_count: {summary['hallucinated_value_count']}",
        f"- invalid_source_row_reference_count: {summary['invalid_source_row_reference_count']}",
        f"- bad_eps_ratio_count: {summary['bad_eps_ratio_count']}",
        f"- requires_human_approval_count: {summary['requires_human_approval_count']}",
        "",
        "## Safety",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        "",
        "## Decision",
        f"- ready_for_stage7p_ai_suggestion_queue_integration: {summary['ready_for_stage7p_ai_suggestion_queue_integration']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
