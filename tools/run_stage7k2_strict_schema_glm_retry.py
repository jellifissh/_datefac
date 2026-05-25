import json
import os
import sys
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
IN_LOWRATE_SUMMARY = BASE_DIR / "output" / "stage7k_retry_lowrate_glm_api_sandbox" / "191_stage7k_retry_lowrate_summary.json"
IN_SELECTED_REQ = BASE_DIR / "output" / "stage7k_retry_lowrate_glm_api_sandbox" / "191_stage7k_selected_single_request.json"
IN_SCHEMA = BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_ai_review_response_schema.json"
IN_RULES = BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_ai_validation_rules.json"

OUT_DIR = BASE_DIR / "output" / "stage7k2_strict_schema_glm_retry"
OUT_SUMMARY = OUT_DIR / "192_stage7k2_strict_schema_summary.json"
OUT_REPORT = OUT_DIR / "192_stage7k2_strict_schema_report.md"
OUT_SELECTED = OUT_DIR / "192_stage7k2_selected_request.json"
OUT_RAW = OUT_DIR / "192_stage7k2_raw_response_sanitized.json"
OUT_VALID = OUT_DIR / "192_stage7k2_validation_result.json"

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


def _build_strict_prompt(req: Dict[str, Any], schema: Dict[str, Any]) -> str:
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
                "source_excerpt": _norm(row.get("source_text_excerpt"))[:200],
            }
        )

    required_fields = schema.get("required", [])
    payload = {
        "review_id": _norm(req.get("review_id")),
        "conflict_reason": _norm(req.get("manual_review_reason")),
        "candidate_rows": compact_rows,
        "rules": {
            "eps_must_not_be_ratio": True,
            "suggested_value_must_come_from_candidate_rows": True,
            "suggested_row_ids_must_exist": True,
        },
    }

    strict_template = {
        "review_id": _norm(req.get("review_id")),
        "suggested_action": "keep_manual_review",
        "suggested_row_ids": [],
        "suggested_metric_name": "",
        "suggested_year": "",
        "suggested_value": "",
        "suggested_unit": "",
        "confidence": 0.0,
        "reasoning_summary": "证据不足，保留人工复核",
        "risk_flags": ["insufficient_evidence"],
        "requires_human_approval": True,
    }

    return (
        "你是严格 JSON 输出器。\n"
        "只输出一个 JSON object，不要 Markdown，不要额外解释。\n"
        "必须包含全部必填字段，缺失字段视为错误。必填字段："
        + ", ".join(required_fields)
        + "\n"
        "字段规则：\n"
        "1) suggested_row_ids 必须是数组；2) risk_flags 必须是数组；\n"
        "3) confidence 必须是 0 到 1 数字；4) requires_human_approval 必须是 true；\n"
        "5) 无法判断时 suggested_action=keep_manual_review；\n"
        "6) suggested_value 只能来自 candidate_rows；\n"
        "7) suggested_row_ids 只能引用 candidate_rows.row_id；\n"
        "8) EPS/每股收益不得使用 ratio 或 % 作为单位。\n"
        "输出结构示例（必须按同字段返回，可改值）：\n"
        + json.dumps(strict_template, ensure_ascii=False)
        + "\n输入请求："
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


def _schema_validate(resp_obj: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    errs: List[str] = []
    missing: List[str] = []
    required = schema.get("required", [])
    props = schema.get("properties", {})
    for key in required:
        if key not in resp_obj:
            errs.append(f"missing_required:{key}")
            missing.append(key)

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
    return errs, missing


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

    sv = _norm(resp_obj.get("suggested_value"))
    if selected_rows and sv and sv not in allowed_values:
        hallucinated += 1
        errs.append("hallucinated_value")

    is_eps = False
    for r in req.get("candidate_rows", []):
        joined = (_norm(r.get("normalized_metric_name")) + " " + _norm(r.get("raw_metric_name"))).lower()
        if "eps" in joined or "每股收益" in joined:
            is_eps = True
            break
    su = _norm(resp_obj.get("suggested_unit"))
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
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    before = _snapshot_hashes()

    for p in [IN_LOWRATE_SUMMARY, IN_SELECTED_REQ, IN_SCHEMA, IN_RULES]:
        if not p.exists():
            summary = {
                "stage": "stage7k2_strict_schema_glm_retry",
                "mode": "blocked_missing_input",
                "based_on_stage7k_lowrate_commit": "5f67081158ded9b7d5641cb2124ac81ffdfda39b",
                "selected_review_request_count": 0,
                "external_api_called": False,
                "provider": "openai_compatible",
                "model": _norm(os.environ.get("AI_REVIEW_MODEL", "")),
                "http_status": None,
                "rate_limited": False,
                "timeout": False,
                "real_api_response_count": 0,
                "schema_valid_response_count": 0,
                "schema_invalid_response_count": 0,
                "validated_suggestion_count": 0,
                "rejected_suggestion_count": 0,
                "missing_required_fields": [],
                "hallucinated_value_count": 0,
                "invalid_source_row_reference_count": 0,
                "bad_eps_ratio_count": 0,
                "requires_human_approval_count": 0,
                "production_files_modified": False,
                "official_02b_modified": False,
                "formal_rules_modified": False,
                "standardizer_modified": False,
                "release_package_modified": False,
                "check_delivery_state_overall_status": _norm(_run_delivery_check().get("overall_status")),
                "ready_for_stage7l_ai_output_evaluation": False,
            }
            _write_json(OUT_SUMMARY, summary)
            OUT_REPORT.write_text(f"# Stage7K2 Blocked\n\n- missing input: {p}\n", encoding="utf-8")
            return 0

    req = json.loads(IN_SELECTED_REQ.read_text(encoding="utf-8"))
    _write_json(OUT_SELECTED, req)
    schema = json.loads(IN_SCHEMA.read_text(encoding="utf-8"))

    api_key = os.environ.get("AI_REVIEW_API_KEY", "")
    base_url = os.environ.get("AI_REVIEW_BASE_URL", "")
    model = os.environ.get("AI_REVIEW_MODEL", "")

    timeout_seconds = 90
    max_tokens = 1000
    temperature = 0
    external_api_called = False
    http_status = None
    rate_limited = False
    timed_out = False
    response_json_ok = False
    parse_method = ""
    raw_error = ""
    resp_obj: Dict[str, Any] = {}

    if not args.enable_external_api:
        raw_error = "flag_required:--enable-external-api"
    elif not (_norm(api_key) and _norm(base_url) and _norm(model)):
        raw_error = "missing_env:AI_REVIEW_API_KEY_or_AI_REVIEW_BASE_URL_or_AI_REVIEW_MODEL"
    else:
        external_api_called = True
        endpoint = base_url.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        prompt = _build_strict_prompt(req, schema)
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You must return one strict JSON object only."},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }

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
                resp_obj, parse_method = _parse_json_content(msg_content)
                response_json_ok = True
        except requests.exceptions.Timeout:
            timed_out = True
            raw_error = "timeout"
        except Exception as e:
            raw_error = f"request_error:{e.__class__.__name__}:{_norm(e)}"

    schema_errors: List[str] = []
    missing_fields: List[str] = []
    logic = {
        "errors": ["response_not_available"],
        "validation_pass": False,
        "hallucinated_value_count": 0,
        "invalid_source_row_reference_count": 0,
        "bad_eps_ratio_count": 0,
    }

    if response_json_ok:
        schema_errors, missing_fields = _schema_validate(resp_obj, schema)
        if not schema_errors:
            logic = _logic_validate(req, resp_obj)
        else:
            logic = {
                "errors": schema_errors,
                "validation_pass": False,
                "hallucinated_value_count": 0,
                "invalid_source_row_reference_count": 0,
                "bad_eps_ratio_count": 0,
            }

    schema_valid_count = 1 if (response_json_ok and not schema_errors) else 0
    schema_invalid_count = 1 if (external_api_called and schema_valid_count == 0) else 0
    validated_count = 1 if (schema_valid_count == 1 and logic["validation_pass"]) else 0
    rejected_count = 1 if (external_api_called and validated_count == 0) else 0
    requires_human_approval_count = 1 if bool(resp_obj.get("requires_human_approval", False)) else 0

    _write_json(
        OUT_RAW,
        {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "external_api_called": external_api_called,
            "http_status": http_status,
            "rate_limited": rate_limited,
            "timeout": timed_out,
            "parse_method": parse_method,
            "response_json_parse_success": response_json_ok,
            "response_obj": resp_obj if response_json_ok else {},
            "error": raw_error,
        },
    )

    _write_json(
        OUT_VALID,
        {
            "review_id": _norm(req.get("review_id")),
            "schema_errors": schema_errors,
            "missing_required_fields": missing_fields,
            "logic_errors": logic["errors"],
            "validation_pass": bool(logic["validation_pass"]) and not schema_errors,
            "hallucinated_value_count": logic["hallucinated_value_count"],
            "invalid_source_row_reference_count": logic["invalid_source_row_reference_count"],
            "bad_eps_ratio_count": logic["bad_eps_ratio_count"],
            "requires_human_approval": bool(resp_obj.get("requires_human_approval", False)),
        },
    )

    after = _snapshot_hashes()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]
    overall_status = _norm(_run_delivery_check().get("overall_status"))

    summary = {
        "stage": "stage7k2_strict_schema_glm_retry",
        "mode": "real_api_single_request_strict_schema",
        "based_on_stage7k_lowrate_commit": "5f67081158ded9b7d5641cb2124ac81ffdfda39b",
        "selected_review_request_count": 1,
        "external_api_called": external_api_called,
        "provider": "openai_compatible",
        "model": _norm(model) or "glm-4.7",
        "http_status": http_status,
        "rate_limited": rate_limited,
        "timeout": timed_out,
        "real_api_response_count": 1 if response_json_ok else 0,
        "schema_valid_response_count": schema_valid_count,
        "schema_invalid_response_count": schema_invalid_count,
        "validated_suggestion_count": validated_count,
        "rejected_suggestion_count": rejected_count,
        "missing_required_fields": missing_fields,
        "hallucinated_value_count": logic["hallucinated_value_count"],
        "invalid_source_row_reference_count": logic["invalid_source_row_reference_count"],
        "bad_eps_ratio_count": logic["bad_eps_ratio_count"],
        "requires_human_approval_count": requires_human_approval_count,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": overall_status,
        "ready_for_stage7l_ai_output_evaluation": bool(
            response_json_ok
            and schema_valid_count == 1
            and validated_count == 1
            and overall_status == "PASS"
            and not production_files_modified
            and not official_02b_modified
            and not formal_rules_modified
            and not standardizer_modified
            and not release_package_modified
        ),
    }
    _write_json(OUT_SUMMARY, summary)

    OUT_REPORT.write_text(
        "\n".join(
            [
                "# Stage7K2 Strict Schema GLM Retry",
                "",
                "## Runtime",
                f"- selected_review_request_count: {summary['selected_review_request_count']}",
                f"- external_api_called: {summary['external_api_called']}",
                f"- http_status: {summary['http_status']}",
                f"- rate_limited: {summary['rate_limited']}",
                f"- timeout: {summary['timeout']}",
                "",
                "## Validation",
                f"- schema_valid/invalid: {summary['schema_valid_response_count']}/{summary['schema_invalid_response_count']}",
                f"- missing_required_fields: {summary['missing_required_fields']}",
                f"- validated/rejected: {summary['validated_suggestion_count']}/{summary['rejected_suggestion_count']}",
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
                f"- ready_for_stage7l_ai_output_evaluation: {summary['ready_for_stage7l_ai_output_evaluation']}",
            ]
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

