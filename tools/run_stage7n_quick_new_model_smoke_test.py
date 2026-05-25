import json
import os
import socket
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

import requests

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

BASE_DIR = Path(r"D:\_datefac")
IN_SLIM_REQ = BASE_DIR / "output" / "stage7m_fix_request_slimming" / "195_stage7m_slim_selected_requests.jsonl"
IN_STAGE7I_REQ = BASE_DIR / "output" / "stage7i_ai_runtime_dry_run" / "188_stage7i_ai_review_requests.jsonl"
IN_SCHEMA = BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_ai_review_response_schema.json"
IN_RULES = BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_ai_validation_rules.json"

OUT_DIR = BASE_DIR / "output" / "stage7n_quick_new_model_smoke_test"
OUT_SUMMARY = OUT_DIR / "198_stage7n_quick_new_model_summary.json"
OUT_REPORT = OUT_DIR / "198_stage7n_quick_new_model_report.md"
OUT_SELECTED = OUT_DIR / "198_stage7n_selected_request.json"
OUT_RAW = OUT_DIR / "198_stage7n_raw_response_sanitized.json"
OUT_VALID = OUT_DIR / "198_stage7n_validation_result.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"


def _norm(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


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


def _sanitize_base_url(base_url: str) -> str:
    if not _norm(base_url):
        return ""
    parsed = urlparse(base_url)
    host = parsed.hostname or ""
    scheme = parsed.scheme or "https"
    path = parsed.path or ""
    return f"{scheme}://{host}{path}"


def _socket_test(host: str, port: int = 443, timeout_seconds: int = 10) -> Tuple[bool, str]:
    try:
        s = socket.create_connection((host, port), timeout_seconds)
        s.close()
        return True, "ok"
    except Exception as e:
        return False, f"{e.__class__.__name__}:{_norm(e)}"


def _choose_one_request() -> Tuple[Dict[str, Any], str]:
    if IN_SLIM_REQ.exists():
        rows = _load_jsonl(IN_SLIM_REQ)
        if rows:
            return rows[0], "stage7m_fix_slim_requests"
    rows = _load_jsonl(IN_STAGE7I_REQ)
    rows = sorted(rows, key=lambda x: (len(x.get("candidate_rows", [])), _norm(x.get("review_id"))))
    return rows[0], "stage7i_requests_fallback"


def _build_prompt(req: Dict[str, Any], schema: Dict[str, Any]) -> str:
    required = schema.get("required", [])
    payload = {
        "review_id": _norm(req.get("review_id")),
        "manual_review_reason": _norm(req.get("manual_review_reason")),
        "candidate_rows": req.get("candidate_rows", []),
        "known_rules": req.get("known_rules", {"eps_unit": "元/股", "do_not_use_ratio_for_eps": True}),
    }
    return (
        "只输出一个 JSON object，不允许 Markdown，不允许 JSON 外解释文字。\n"
        "必须包含字段：" + ", ".join(required) + "。\n"
        "规则：suggested_row_ids 必须来自 candidate_rows；suggested_value 不得编造；"
        "suggested_unit 必须来自候选或规则允许范围；confidence 0~1；risk_flags 数组；"
        "requires_human_approval=true；EPS/每股收益不得 ratio。\n"
        "如果无法判断，必须使用 keep_manual_review 且保留完整字段。\n"
        "输入：" + json.dumps(payload, ensure_ascii=False)
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
            errors.append(f"missing_required:{k}")
            missing.append(k)

    tmap = {"string": str, "number": (int, float), "array": list, "boolean": bool}
    for k, spec in props.items():
        if k not in resp:
            continue
        et = spec.get("type")
        if et in tmap and not isinstance(resp[k], tmap[et]):
            errors.append(f"type_mismatch:{k}:{et}")

    enum = props.get("suggested_action", {}).get("enum", [])
    if enum and _norm(resp.get("suggested_action")) not in set(enum):
        errors.append("suggested_action_enum_invalid")

    try:
        c = float(resp.get("confidence"))
        if c < 0 or c > 1:
            errors.append("confidence_out_of_range")
    except Exception:
        errors.append("confidence_not_numeric")

    return errors, missing


def _logic_validate(req: Dict[str, Any], resp: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    hallucinated = 0
    invalid_ref = 0
    bad_eps_ratio = 0

    row_map = {_norm(r.get("row_id")): r for r in req.get("candidate_rows", [])}
    selected_ids = [_norm(x) for x in resp.get("suggested_row_ids", [])]
    action = _norm(resp.get("suggested_action"))

    for rid in selected_ids:
        if rid not in row_map:
            invalid_ref += 1
            errors.append("invalid_source_row_reference")
            break

    if action == "accept_one" and len(selected_ids) != 1:
        errors.append("accept_one_requires_single_row")
    if action in {"accept_one", "merge_same_value", "exclude"} and not selected_ids:
        errors.append("action_requires_row_ids")

    selected_rows = [row_map[rid] for rid in selected_ids if rid in row_map]
    if selected_rows:
        values = {_norm(r.get("value")) for r in selected_rows}
        units = {_norm(r.get("unit")) for r in selected_rows}
        if _norm(resp.get("suggested_value")) and _norm(resp.get("suggested_value")) not in values:
            hallucinated += 1
            errors.append("hallucinated_value")
        if _norm(resp.get("suggested_unit")) and _norm(resp.get("suggested_unit")) not in units:
            errors.append("suggested_unit_not_in_candidate")

    metric_text = " ".join(
        [(_norm(r.get("normalized_metric_name")) + " " + _norm(r.get("raw_metric_name"))).lower() for r in req.get("candidate_rows", [])]
    )
    if ("eps" in metric_text or "每股收益" in metric_text) and _norm(resp.get("suggested_unit")) in {"ratio", "%"}:
        bad_eps_ratio += 1
        errors.append("eps_ratio_forbidden")

    if not bool(resp.get("requires_human_approval", False)):
        errors.append("requires_human_approval_must_be_true")

    return {
        "errors": errors,
        "validation_pass": len(errors) == 0,
        "hallucinated_value_count": hallucinated,
        "invalid_source_row_reference_count": invalid_ref,
        "bad_eps_ratio_count": bad_eps_ratio,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    required = [IN_SCHEMA, IN_RULES]
    for p in required:
        if not p.exists():
            _write_json(
                OUT_SUMMARY,
                {
                    "stage": "stage7n_quick_new_model_smoke_test",
                    "mode": "blocked_missing_input",
                    "external_api_called": False,
                    "blocked_reason": f"missing_input:{p}",
                },
            )
            return 0

    before = _snapshot_hashes()
    schema = _load_json(IN_SCHEMA)
    _rules = _load_json(IN_RULES)
    req, request_source = _choose_one_request()
    _write_json(OUT_SELECTED, req)

    api_key = os.environ.get("AI_REVIEW_API_KEY", "")
    base_url = os.environ.get("AI_REVIEW_BASE_URL", "")
    model = os.environ.get("AI_REVIEW_MODEL", "")

    api_key_present = bool(_norm(api_key))
    base_url_present = bool(_norm(base_url))
    model_present = bool(_norm(model))
    base_url_sanitized = _sanitize_base_url(base_url)

    parsed = urlparse(base_url) if _norm(base_url) else None
    socket_host = (parsed.hostname if parsed and parsed.hostname else "open.bigmodel.cn")
    socket_ok, socket_error = _socket_test(socket_host, 443, timeout_seconds=10)

    timeout_seconds = 120
    max_tokens = 700
    temperature = 0
    external_api_called = False
    http_status = None
    rate_limited = False
    timed_out = False
    latency_seconds = None
    parse_method = ""
    response_json_parse_success = False
    parsed_obj: Dict[str, Any] = {}
    error_type = ""
    error_summary = ""
    schema_errors: List[str] = []
    missing_required_fields: List[str] = []
    logic = {
        "errors": ["response_not_available"],
        "validation_pass": False,
        "hallucinated_value_count": 0,
        "invalid_source_row_reference_count": 0,
        "bad_eps_ratio_count": 0,
    }

    if socket_ok and api_key_present and base_url_present and model_present:
        external_api_called = True
        endpoint = base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Return only one strict JSON object."},
                {"role": "user", "content": _build_prompt(req, schema)},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        t0 = time.time()
        try:
            resp = requests.post(endpoint, headers=headers, json=payload, timeout=timeout_seconds)
            latency_seconds = round(time.time() - t0, 3)
            http_status = resp.status_code
            if resp.status_code == 401:
                error_type = "http_401"
                error_summary = "HTTP 401 Unauthorized"
            elif resp.status_code == 403:
                error_type = "http_403"
                error_summary = "HTTP 403 Forbidden"
            elif resp.status_code == 404:
                error_type = "http_404"
                error_summary = "HTTP 404 Not Found"
            elif resp.status_code == 429:
                rate_limited = True
                error_type = "http_429"
                error_summary = "HTTP 429 Rate Limited"
            elif resp.status_code >= 400:
                error_type = "connection_error"
                error_summary = f"HTTP {resp.status_code}"
            else:
                data = resp.json()
                content = ""
                if isinstance(data, dict):
                    choices = data.get("choices", [])
                    if choices:
                        content = _norm(choices[0].get("message", {}).get("content"))
                parsed_obj, parse_method = _parse_json_content(content)
                response_json_parse_success = True
                schema_errors, missing_required_fields = _schema_validate(parsed_obj, schema)
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
                    error_summary = "Schema validation failed"
        except requests.exceptions.Timeout:
            latency_seconds = round(time.time() - t0, 3)
            timed_out = True
            error_type = "timeout"
            error_summary = "Request timeout"
        except Exception as e:
            latency_seconds = round(time.time() - t0, 3)
            error_type = "connection_error"
            error_summary = f"{e.__class__.__name__}:{_norm(e)}"
    else:
        if not socket_ok:
            error_type = "connection_error"
            error_summary = f"socket_test_failed:{socket_error}"
        elif not api_key_present:
            error_type = "connection_error"
            error_summary = "missing_api_key"
        elif not base_url_present:
            error_type = "connection_error"
            error_summary = "missing_base_url"
        elif not model_present:
            error_type = "connection_error"
            error_summary = "missing_model"

    schema_valid_response_count = 1 if (response_json_parse_success and len(schema_errors) == 0) else 0
    schema_invalid_response_count = 1 if (external_api_called and schema_valid_response_count == 0) else 0
    real_api_response_count = 1 if response_json_parse_success else 0
    validated_suggestion_count = 1 if (schema_valid_response_count == 1 and logic["validation_pass"]) else 0
    rejected_suggestion_count = 1 if (external_api_called and validated_suggestion_count == 0) else 0
    requires_human_approval_count = 1 if bool(parsed_obj.get("requires_human_approval", False)) else 0

    hallucinated_value_count = logic["hallucinated_value_count"]
    invalid_source_row_reference_count = logic["invalid_source_row_reference_count"]
    bad_eps_ratio_count = logic["bad_eps_ratio_count"]

    if external_api_called and schema_valid_response_count == 0 and not error_type:
        error_type = "schema_invalid"
        error_summary = "schema invalid response"
    if external_api_called and schema_valid_response_count == 1 and logic["validation_pass"] and hallucinated_value_count > 0:
        error_type = "hallucinated_value"
    if external_api_called and schema_valid_response_count == 1 and logic["validation_pass"] and invalid_source_row_reference_count > 0:
        error_type = "invalid_source_row_reference"

    after = _snapshot_hashes()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]
    delivery = _run_delivery_check()
    check_status = _norm(delivery.get("overall_status"))

    new_model_smoke_test_pass = bool(
        schema_valid_response_count == 1
        and hallucinated_value_count == 0
        and invalid_source_row_reference_count == 0
        and bad_eps_ratio_count == 0
    )

    if not socket_ok:
        recommended_next_step = "fix_socket_connectivity_then_retry_stage7n_quick"
    elif rate_limited:
        recommended_next_step = "check_provider_rate_limits_and_retry_later"
    elif timed_out:
        recommended_next_step = "increase_timeout_or_reduce_prompt_then_retry"
    elif schema_invalid_response_count == 1:
        recommended_next_step = "tighten_strict_schema_prompt_and_retry_single_case"
    elif new_model_smoke_test_pass:
        recommended_next_step = "proceed_to_stage7n_batch_policy_with_guardrails"
    else:
        recommended_next_step = "investigate_validation_failures_before_expansion"

    raw_out = {
        "external_api_called": external_api_called,
        "socket_host": socket_host,
        "socket_ok": socket_ok,
        "http_status": http_status,
        "rate_limited": rate_limited,
        "timeout": timed_out,
        "latency_seconds": latency_seconds,
        "parse_method": parse_method,
        "response_json_parse_success": response_json_parse_success,
        "response_obj": parsed_obj if response_json_parse_success else {},
        "error_type": error_type,
        "error_summary": error_summary,
    }
    _write_json(OUT_RAW, raw_out)

    validation_out = {
        "review_id": _norm(req.get("review_id")),
        "schema_errors": schema_errors,
        "missing_required_fields": missing_required_fields,
        "logic_errors": logic["errors"],
        "validation_pass": bool(schema_valid_response_count == 1 and logic["validation_pass"]),
        "hallucinated_value_count": hallucinated_value_count,
        "invalid_source_row_reference_count": invalid_source_row_reference_count,
        "bad_eps_ratio_count": bad_eps_ratio_count,
        "requires_human_approval": bool(parsed_obj.get("requires_human_approval", False)),
    }
    _write_json(OUT_VALID, validation_out)

    summary = {
        "stage": "stage7n_quick_new_model_smoke_test",
        "mode": "real_api_single_request_strict_schema",
        "external_api_called": external_api_called,
        "provider": "openai_compatible",
        "model": _norm(model),
        "api_key_present": api_key_present,
        "api_key_logged": False,
        "base_url_present": base_url_present,
        "base_url_sanitized": base_url_sanitized,
        "selected_review_request_count": 1,
        "request_source": request_source,
        "socket_host": socket_host,
        "socket_ok": socket_ok,
        "http_status": http_status,
        "rate_limited": rate_limited,
        "timeout": timed_out,
        "real_api_response_count": real_api_response_count,
        "schema_valid_response_count": schema_valid_response_count,
        "schema_invalid_response_count": schema_invalid_response_count,
        "missing_required_fields": missing_required_fields,
        "validated_suggestion_count": validated_suggestion_count,
        "rejected_suggestion_count": rejected_suggestion_count,
        "hallucinated_value_count": hallucinated_value_count,
        "invalid_source_row_reference_count": invalid_source_row_reference_count,
        "bad_eps_ratio_count": bad_eps_ratio_count,
        "requires_human_approval_count": requires_human_approval_count,
        "latency_seconds": latency_seconds,
        "error_type": error_type,
        "error_summary": error_summary,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": check_status,
        "new_model_smoke_test_pass": new_model_smoke_test_pass,
        "recommended_next_step": recommended_next_step,
    }
    _write_json(OUT_SUMMARY, summary)

    report = "\n".join(
        [
            "# Stage7N Quick New Model Smoke Test",
            "",
            "## Runtime",
            f"- model: {summary['model']}",
            f"- base_url_sanitized: {summary['base_url_sanitized']}",
            f"- socket_host/socket_ok: {summary['socket_host']}/{summary['socket_ok']}",
            f"- selected_review_request_count: {summary['selected_review_request_count']}",
            f"- external_api_called: {summary['external_api_called']}",
            "",
            "## Result",
            f"- http_status: {summary['http_status']}",
            f"- rate_limited/timeout: {summary['rate_limited']}/{summary['timeout']}",
            f"- real_api_response_count: {summary['real_api_response_count']}",
            f"- schema_valid/invalid: {summary['schema_valid_response_count']}/{summary['schema_invalid_response_count']}",
            f"- missing_required_fields: {summary['missing_required_fields']}",
            f"- validated/rejected: {summary['validated_suggestion_count']}/{summary['rejected_suggestion_count']}",
            f"- hallucinated_value_count: {summary['hallucinated_value_count']}",
            f"- invalid_source_row_reference_count: {summary['invalid_source_row_reference_count']}",
            f"- bad_eps_ratio_count: {summary['bad_eps_ratio_count']}",
            f"- requires_human_approval_count: {summary['requires_human_approval_count']}",
            f"- latency_seconds: {summary['latency_seconds']}",
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
            f"- new_model_smoke_test_pass: {summary['new_model_smoke_test_pass']}",
            f"- recommended_next_step: {summary['recommended_next_step']}",
        ]
    )
    OUT_REPORT.write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

