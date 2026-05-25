import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

BASE_DIR = Path(r"D:\_datefac")
IN_REQUESTS = BASE_DIR / "output" / "stage7i_ai_runtime_dry_run" / "188_stage7i_ai_review_requests.jsonl"
IN_SCHEMA = BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_ai_review_response_schema.json"
IN_RULES = BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_ai_validation_rules.json"

OUT_DIR = BASE_DIR / "output" / "stage7k_retry_lowrate_glm_api_sandbox"
OUT_SUMMARY = OUT_DIR / "191_stage7k_retry_lowrate_summary.json"
OUT_REPORT = OUT_DIR / "191_stage7k_retry_lowrate_report.md"
OUT_SELECTED = OUT_DIR / "191_stage7k_selected_single_request.json"
OUT_RAW = OUT_DIR / "191_stage7k_raw_response_sanitized.json"
OUT_VALID = OUT_DIR / "191_stage7k_validation_result.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"


def _norm(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


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


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _select_single_non_eps(requests_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    def is_eps_row(req: Dict[str, Any]) -> bool:
        for r in req.get("candidate_rows", []):
            nm = _norm(r.get("normalized_metric_name")).lower()
            rm = _norm(r.get("raw_metric_name")).lower()
            if "eps" in nm or "每股收益" in nm or "eps" in rm or "每股收益" in rm:
                return True
        return False

    non_eps = [r for r in requests_rows if not is_eps_row(r)]
    pool = non_eps if non_eps else requests_rows
    pool = sorted(pool, key=lambda x: (len(x.get("candidate_rows", [])), _norm(x.get("review_id"))))
    return pool[0]


def _build_min_prompt(req: Dict[str, Any]) -> str:
    compact_rows = []
    for row in req.get("candidate_rows", []):
        compact_rows.append(
            {
                "row_id": _norm(row.get("row_id")),
                "metric": _norm(row.get("normalized_metric_name")) or _norm(row.get("raw_metric_name")),
                "year": _norm(row.get("year")),
                "value": _norm(row.get("value")),
                "unit": _norm(row.get("unit")),
                "statement_type": _norm(row.get("statement_type")),
                "source_excerpt": _norm(row.get("source_text_excerpt"))[:180],
            }
        )

    payload = {
        "review_id": _norm(req.get("review_id")),
        "conflict_reason": _norm(req.get("manual_review_reason")),
        "candidate_rows": compact_rows,
        "known_rules": {"eps_must_not_be_ratio": True},
    }
    return (
        "Return exactly one JSON object only, no markdown.\n"
        "Use suggested_action in: accept_one, merge_same_value, split_metric, exclude, keep_manual_review.\n"
        "If evidence is weak, choose keep_manual_review.\n"
        "requires_human_approval must be true.\n"
        "INPUT_JSON="
        + json.dumps(payload, ensure_ascii=False)
    )


def _parse_json_content(raw_text: str) -> Tuple[Dict[str, Any], str]:
    txt = _norm(raw_text)
    if not txt:
        raise ValueError("empty_content")
    try:
        return json.loads(txt), "raw_json"
    except Exception:
        pass
    if "```" in txt:
        parts = txt.split("```")
        for part in parts:
            s = part.strip()
            if s.startswith("json"):
                s = s[4:].strip()
            if s.startswith("{") and s.endswith("}"):
                return json.loads(s), "fence_repair"
    li = txt.find("{")
    ri = txt.rfind("}")
    if li >= 0 and ri > li:
        return json.loads(txt[li : ri + 1]), "slice_repair"
    raise ValueError("json_parse_failed")


def _schema_validate(resp_obj: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    required = schema.get("required", [])
    props = schema.get("properties", {})
    for key in required:
        if key not in resp_obj:
            errs.append(f"missing_required:{key}")

    expected = {
        "string": str,
        "array": list,
        "number": (int, float),
        "boolean": bool,
    }
    for key, conf in props.items():
        if key not in resp_obj:
            continue
        t = conf.get("type")
        if t in expected and not isinstance(resp_obj[key], expected[t]):
            errs.append(f"type_mismatch:{key}:{t}")

    allowed_actions = props.get("suggested_action", {}).get("enum", [])
    if allowed_actions and _norm(resp_obj.get("suggested_action")) not in set(allowed_actions):
        errs.append("invalid_suggested_action")

    try:
        conf = float(resp_obj.get("confidence"))
        if conf < 0 or conf > 1:
            errs.append("confidence_out_of_range")
    except Exception:
        errs.append("confidence_not_numeric")
    return errs


def _logic_validate(req: Dict[str, Any], resp_obj: Dict[str, Any]) -> Dict[str, Any]:
    errs: List[str] = []
    hallucinated = 0
    invalid_ref = 0
    bad_eps_ratio = 0

    row_map = {_norm(r.get("row_id")): r for r in req.get("candidate_rows", [])}
    picked_ids = [_norm(x) for x in resp_obj.get("suggested_row_ids", [])]
    action = _norm(resp_obj.get("suggested_action"))

    for rid in picked_ids:
        if rid not in row_map:
            invalid_ref += 1
            errs.append("invalid_source_row_reference")
            break

    if action == "accept_one" and len(picked_ids) != 1:
        errs.append("accept_one_requires_exactly_one_row")
    if action in {"accept_one", "merge_same_value", "exclude"} and not picked_ids:
        errs.append("action_requires_row_ids")

    selected_rows = [row_map[rid] for rid in picked_ids if rid in row_map]
    allowed_values = {_norm(r.get("value")) for r in selected_rows}
    allowed_units = {_norm(r.get("unit")) for r in selected_rows}

    sv = _norm(resp_obj.get("suggested_value"))
    su = _norm(resp_obj.get("suggested_unit"))
    if selected_rows and sv and sv not in allowed_values:
        hallucinated += 1
        errs.append("hallucinated_value")
    if selected_rows and su and su not in allowed_units:
        errs.append("suggested_unit_not_in_candidates")

    is_eps = False
    for r in req.get("candidate_rows", []):
        joined = (_norm(r.get("normalized_metric_name")) + " " + _norm(r.get("raw_metric_name"))).lower()
        if "eps" in joined or "每股收益" in joined:
            is_eps = True
            break
    if is_eps and su in {"ratio", "%"}:
        bad_eps_ratio += 1
        errs.append("eps_ratio_forbidden")

    if not bool(resp_obj.get("requires_human_approval", False)):
        errs.append("requires_human_approval_must_be_true")

    return {
        "errors": errs,
        "validation_pass": len(errs) == 0,
        "hallucinated_value_count": hallucinated,
        "invalid_source_row_reference_count": invalid_ref,
        "bad_eps_ratio_count": bad_eps_ratio,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--enable-external-api", action="store_true")
    parser.add_argument("--retry-once", action="store_true", help="Optional single retry after >=10s.")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    before = _snapshot_hashes()
    delivery_before = _run_delivery_check()

    api_key = os.environ.get("AI_REVIEW_API_KEY", "")
    base_url = os.environ.get("AI_REVIEW_BASE_URL", "")
    model = os.environ.get("AI_REVIEW_MODEL", "")
    api_key_present = bool(_norm(api_key))
    base_url_present = bool(_norm(base_url))
    model_present = bool(_norm(model))

    if not IN_REQUESTS.exists() or not IN_SCHEMA.exists() or not IN_RULES.exists():
        summary = {
            "stage": "stage7k_retry_lowrate_glm_api_sandbox",
            "mode": "blocked_missing_input",
            "selected_review_request_count": 0,
            "external_api_called": False,
            "provider": "openai_compatible",
            "model": _norm(model),
            "api_key_present": api_key_present,
            "api_key_logged": False,
            "timeout_seconds": 90,
            "max_tokens": 800,
            "retry_count": 0,
            "http_status": None,
            "rate_limited": False,
            "timeout": False,
            "real_api_response_count": 0,
            "schema_valid_response_count": 0,
            "schema_invalid_response_count": 0,
            "validated_suggestion_count": 0,
            "rejected_suggestion_count": 0,
            "hallucinated_value_count": 0,
            "invalid_source_row_reference_count": 0,
            "bad_eps_ratio_count": 0,
            "production_files_modified": False,
            "official_02b_modified": False,
            "formal_rules_modified": False,
            "standardizer_modified": False,
            "release_package_modified": False,
            "check_delivery_state_overall_status": _norm(delivery_before.get("overall_status")),
            "ready_for_stage7l_ai_output_evaluation": False,
            "recommended_next_step": "补齐 Stage7H/Stage7I 输入文件后重试。",
        }
        _write_json(OUT_SUMMARY, summary)
        OUT_REPORT.write_text("# Stage7K Retry LowRate Blocked\n\n- missing required input files.\n", encoding="utf-8")
        return 0

    requests_rows = [json.loads(line) for line in IN_REQUESTS.read_text(encoding="utf-8").splitlines() if line.strip()]
    selected = _select_single_non_eps(requests_rows)
    _write_json(OUT_SELECTED, selected)

    timeout_seconds = 90
    max_tokens = 800
    retry_count = 0
    external_api_called = False

    http_status = None
    rate_limited = False
    timed_out = False
    parse_method = ""
    response_json_ok = False
    raw_error = ""
    response_obj: Dict[str, Any] = {}

    if not args.enable_external_api:
        raw_error = "flag_required:--enable-external-api"
    elif not api_key_present or not base_url_present or not model_present:
        raw_error = "missing_env:AI_REVIEW_API_KEY_or_AI_REVIEW_BASE_URL_or_AI_REVIEW_MODEL"
    else:
        external_api_called = True
        prompt = _build_min_prompt(selected)
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a strict JSON assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        endpoint = base_url.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        attempts_allowed = 2 if args.retry_once else 1
        for attempt_i in range(1, attempts_allowed + 1):
            try:
                resp = requests.post(endpoint, headers=headers, json=payload, timeout=timeout_seconds)
                http_status = resp.status_code
                if resp.status_code == 429:
                    rate_limited = True
                    raw_error = "http_429"
                elif resp.status_code >= 400:
                    raw_error = f"http_{resp.status_code}"
                else:
                    data = resp.json()
                    msg_content = ""
                    if isinstance(data, dict):
                        choices = data.get("choices", [])
                        if choices:
                            msg_content = _norm(choices[0].get("message", {}).get("content"))
                    response_obj, parse_method = _parse_json_content(msg_content)
                    response_json_ok = True
                    raw_error = ""
                    break
            except requests.exceptions.Timeout:
                timed_out = True
                raw_error = "timeout"
            except Exception as e:
                raw_error = f"request_error:{e.__class__.__name__}:{_norm(e)}"

            if attempt_i < attempts_allowed:
                retry_count += 1
                time.sleep(10)

    schema = json.loads(IN_SCHEMA.read_text(encoding="utf-8"))
    schema_errors: List[str] = []
    logic = {
        "errors": ["response_not_available"],
        "validation_pass": False,
        "hallucinated_value_count": 0,
        "invalid_source_row_reference_count": 0,
        "bad_eps_ratio_count": 0,
    }

    if response_json_ok:
        schema_errors = _schema_validate(response_obj, schema)
        if not schema_errors:
            logic = _logic_validate(selected, response_obj)
        else:
            logic = {
                "errors": schema_errors,
                "validation_pass": False,
                "hallucinated_value_count": 0,
                "invalid_source_row_reference_count": 0,
                "bad_eps_ratio_count": 0,
            }

    schema_valid_count = 1 if (response_json_ok and not schema_errors) else 0
    schema_invalid_count = 1 if external_api_called and schema_valid_count == 0 else 0
    validated_count = 1 if (schema_valid_count == 1 and logic["validation_pass"]) else 0
    rejected_count = 1 if external_api_called and validated_count == 0 else 0

    raw_sanitized = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "external_api_called": external_api_called,
        "http_status": http_status,
        "rate_limited": rate_limited,
        "timeout": timed_out,
        "parse_method": parse_method,
        "response_json_parse_success": response_json_ok,
        "response_obj": response_obj if response_json_ok else {},
        "error": raw_error,
    }
    _write_json(OUT_RAW, raw_sanitized)

    validation_result = {
        "review_id": _norm(selected.get("review_id")),
        "schema_errors": schema_errors,
        "logic_errors": logic["errors"],
        "validation_pass": bool(logic["validation_pass"]) and not schema_errors,
        "hallucinated_value_count": logic["hallucinated_value_count"],
        "invalid_source_row_reference_count": logic["invalid_source_row_reference_count"],
        "bad_eps_ratio_count": logic["bad_eps_ratio_count"],
    }
    _write_json(OUT_VALID, validation_result)

    after = _snapshot_hashes()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]
    delivery = _run_delivery_check()

    if rate_limited:
        next_step = "429 限流：检查 GLM 控制台额度、RPM/TPM、模型权限；降低频率后再试。"
    elif timed_out:
        next_step = "请求超时：确认 API 基础路径与网络策略，必要时继续压缩 prompt。"
    elif validated_count == 1:
        next_step = "单请求已验证可用，可进入 Stage7L 输出质量评估。"
    else:
        next_step = "响应未通过校验：检查返回 JSON 字段与 schema 映射。"

    summary = {
        "stage": "stage7k_retry_lowrate_glm_api_sandbox",
        "mode": "real_api_single_request_sandbox",
        "selected_review_request_count": 1,
        "external_api_called": external_api_called,
        "provider": "openai_compatible",
        "model": _norm(model) or "glm-4.7",
        "api_key_present": api_key_present,
        "api_key_logged": False,
        "timeout_seconds": timeout_seconds,
        "max_tokens": max_tokens,
        "retry_count": retry_count,
        "http_status": http_status,
        "rate_limited": rate_limited,
        "timeout": timed_out,
        "real_api_response_count": 1 if response_json_ok else 0,
        "schema_valid_response_count": schema_valid_count,
        "schema_invalid_response_count": schema_invalid_count,
        "validated_suggestion_count": validated_count,
        "rejected_suggestion_count": rejected_count,
        "hallucinated_value_count": logic["hallucinated_value_count"],
        "invalid_source_row_reference_count": logic["invalid_source_row_reference_count"],
        "bad_eps_ratio_count": logic["bad_eps_ratio_count"],
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": _norm(delivery.get("overall_status")),
        "ready_for_stage7l_ai_output_evaluation": bool(
            response_json_ok
            and validated_count == 1
            and _norm(delivery.get("overall_status")) == "PASS"
            and not production_files_modified
            and not official_02b_modified
            and not formal_rules_modified
            and not standardizer_modified
            and not release_package_modified
        ),
        "recommended_next_step": next_step,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# Stage 7K Retry LowRate GLM API Sandbox",
        "",
        "## Run Config",
        f"- selected_review_request_count: {summary['selected_review_request_count']}",
        f"- external_api_called: {summary['external_api_called']}",
        f"- timeout_seconds: {summary['timeout_seconds']}",
        f"- max_tokens: {summary['max_tokens']}",
        f"- retry_count: {summary['retry_count']}",
        "",
        "## Result",
        f"- http_status: {summary['http_status']}",
        f"- rate_limited: {summary['rate_limited']}",
        f"- timeout: {summary['timeout']}",
        f"- real_api_response_count: {summary['real_api_response_count']}",
        f"- schema_valid/invalid: {summary['schema_valid_response_count']}/{summary['schema_invalid_response_count']}",
        f"- validated/rejected: {summary['validated_suggestion_count']}/{summary['rejected_suggestion_count']}",
        f"- hallucinated_value_count: {summary['hallucinated_value_count']}",
        f"- invalid_source_row_reference_count: {summary['invalid_source_row_reference_count']}",
        f"- bad_eps_ratio_count: {summary['bad_eps_ratio_count']}",
        "",
        "## Safety",
        f"- api_key_present: {summary['api_key_present']}",
        f"- api_key_logged: {summary['api_key_logged']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        "",
        "## Recommended Next Step",
        f"- {summary['recommended_next_step']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

