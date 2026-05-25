import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import requests

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

BASE_DIR = Path(r"D:\_datefac")
IN_SLIM_REQ = BASE_DIR / "output" / "stage7m_fix_request_slimming" / "195_stage7m_slim_selected_requests.jsonl"
IN_FIX_SUMMARY = BASE_DIR / "output" / "stage7m_fix_request_slimming" / "195_stage7m_fix_request_slimming_summary.json"
IN_SCHEMA = BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_ai_review_response_schema.json"
IN_RULES = BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_ai_validation_rules.json"

OUT_DIR = BASE_DIR / "output" / "stage7m2_slim_three_case_api_dry_run"
OUT_SUMMARY = OUT_DIR / "196_stage7m2_slim_three_case_summary.json"
OUT_REPORT = OUT_DIR / "196_stage7m2_slim_three_case_report.md"
OUT_SELECTED = OUT_DIR / "196_stage7m2_selected_requests.jsonl"
OUT_RAW = OUT_DIR / "196_stage7m2_raw_responses_sanitized.jsonl"
OUT_AUDIT = OUT_DIR / "196_stage7m2_validation_audit.xlsx"
OUT_VALID = OUT_DIR / "196_stage7m2_validated_suggestions.xlsx"
OUT_REJ = OUT_DIR / "196_stage7m2_rejected_suggestions.xlsx"
OUT_COST = OUT_DIR / "196_stage7m2_cost_latency_report.json"

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


def _build_prompt(req: Dict[str, Any], schema: Dict[str, Any]) -> str:
    required_fields = schema.get("required", [])
    payload = {
        "review_id": _norm(req.get("review_id")),
        "manual_review_reason": _norm(req.get("manual_review_reason")),
        "candidate_rows": req.get("candidate_rows", []),
        "known_rules": req.get("known_rules", {"eps_unit": "元/股", "do_not_use_ratio_for_eps": True}),
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
        "你是严格 JSON 输出器。只输出一个 JSON object，不要 markdown，不要解释。\n"
        "必须包含字段：" + ", ".join(required_fields) + "。\n"
        "规则：suggested_row_ids 必须来自 candidate_rows；suggested_value 不得编造；"
        "suggested_unit 必须来自候选或规则允许范围；EPS/每股收益不得 ratio；"
        "confidence 必须0到1；risk_flags必须数组；requires_human_approval必须为true；"
        "无法判断时 suggested_action=keep_manual_review。\n"
        "返回模板：" + json.dumps(strict_template, ensure_ascii=False) + "\n"
        "输入：" + json.dumps(payload, ensure_ascii=False)
    )


def _parse_response_text(text: str) -> Tuple[Dict[str, Any], str]:
    t = _norm(text)
    if not t:
        raise ValueError("empty_response")
    try:
        return json.loads(t), "raw_json"
    except Exception:
        pass
    if "```" in t:
        segments = t.split("```")
        for s in segments:
            x = s.strip()
            if x.startswith("json"):
                x = x[4:].strip()
            if x.startswith("{") and x.endswith("}"):
                return json.loads(x), "fence_repair"
    l = t.find("{")
    r = t.rfind("}")
    if l >= 0 and r > l:
        return json.loads(t[l : r + 1]), "slice_repair"
    raise ValueError("json_parse_failed")


def _schema_validate(resp: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    required = schema.get("required", [])
    props = schema.get("properties", {})
    for k in required:
        if k not in resp:
            errors.append(f"missing_required:{k}")
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
    return errors


def _logic_validate(req: Dict[str, Any], resp: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    hallucinated_value_count = 0
    invalid_source_row_reference_count = 0
    bad_eps_ratio_count = 0

    row_map = {_norm(r.get("row_id")): r for r in req.get("candidate_rows", [])}
    selected_ids = [_norm(x) for x in resp.get("suggested_row_ids", [])]
    action = _norm(resp.get("suggested_action"))

    for rid in selected_ids:
        if rid not in row_map:
            invalid_source_row_reference_count += 1
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
            hallucinated_value_count += 1
            errors.append("hallucinated_value")
        if _norm(resp.get("suggested_unit")) and _norm(resp.get("suggested_unit")) not in units:
            errors.append("suggested_unit_not_in_candidate")

    metric_text = " ".join(
        [(_norm(r.get("normalized_metric_name")) + " " + _norm(r.get("raw_metric_name"))).lower() for r in req.get("candidate_rows", [])]
    )
    if ("eps" in metric_text or "每股收益" in metric_text) and _norm(resp.get("suggested_unit")) in {"ratio", "%"}:
        bad_eps_ratio_count += 1
        errors.append("eps_ratio_forbidden")

    if not bool(resp.get("requires_human_approval", False)):
        errors.append("requires_human_approval_must_be_true")

    return {
        "errors": errors,
        "validation_pass": len(errors) == 0,
        "hallucinated_value_count": hallucinated_value_count,
        "invalid_source_row_reference_count": invalid_source_row_reference_count,
        "bad_eps_ratio_count": bad_eps_ratio_count,
    }


def _is_eps_case(req: Dict[str, Any]) -> bool:
    for r in req.get("candidate_rows", []):
        t = (_norm(r.get("normalized_metric_name")) + " " + _norm(r.get("raw_metric_name"))).lower()
        if "eps" in t or "每股收益" in t:
            return True
    return False


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--enable-external-api", action="store_true")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    required = [IN_SLIM_REQ, IN_FIX_SUMMARY, IN_SCHEMA, IN_RULES]
    for p in required:
        if not p.exists():
            _write_json(
                OUT_SUMMARY,
                {
                    "stage": "stage7m2_slim_three_case_strict_schema_api_dry_run",
                    "mode": "blocked_missing_input",
                    "external_api_called": False,
                    "blocked_reason": f"missing_input:{p}",
                },
            )
            return 0

    before = _snapshot_hashes()

    selected = _load_jsonl(IN_SLIM_REQ)
    fix_summary = _load_json(IN_FIX_SUMMARY)
    schema = _load_json(IN_SCHEMA)
    _rules = _load_json(IN_RULES)

    # Enforce exactly 3 groups
    selected = selected[:3]
    _write_jsonl(OUT_SELECTED, selected)

    api_key = os.environ.get("AI_REVIEW_API_KEY", "")
    base_url = os.environ.get("AI_REVIEW_BASE_URL", "")
    model = os.environ.get("AI_REVIEW_MODEL", "")

    timeout_seconds = 120
    max_tokens = 700
    temperature = 0

    external_api_called = False
    raw_rows: List[Dict[str, Any]] = []
    audits: List[Dict[str, Any]] = []
    validated: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    rate_limited_count = 0
    timeout_count = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_latency_ms = 0
    stop_reason = ""

    if args.enable_external_api and _norm(api_key) and _norm(base_url) and _norm(model):
        external_api_called = True
        endpoint = base_url.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        for i, req in enumerate(selected):
            review_id = _norm(req.get("review_id"))
            prompt = _build_prompt(req, schema)
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "Return one strict JSON object only."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            }

            http_status = None
            rate_limited = False
            timed_out = False
            error = ""
            parsed_obj: Dict[str, Any] = {}
            parse_method = ""
            usage: Dict[str, Any] = {}
            schema_errors: List[str] = []
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
                latency_ms = int((time.time() - t0) * 1000)
                total_latency_ms += latency_ms
                http_status = resp.status_code
                if resp.status_code == 429:
                    rate_limited = True
                    rate_limited_count += 1
                    error = "http_429"
                elif resp.status_code >= 400:
                    error = f"http_{resp.status_code}"
                else:
                    data = resp.json()
                    usage = data.get("usage", {}) if isinstance(data, dict) else {}
                    total_prompt_tokens += int(usage.get("prompt_tokens", 0) or 0)
                    total_completion_tokens += int(usage.get("completion_tokens", 0) or 0)
                    content = ""
                    if isinstance(data, dict):
                        choices = data.get("choices", [])
                        if choices:
                            content = _norm(choices[0].get("message", {}).get("content"))
                    parsed_obj, parse_method = _parse_response_text(content)
                    schema_errors = _schema_validate(parsed_obj, schema)
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
            except requests.exceptions.Timeout:
                latency_ms = int((time.time() - t0) * 1000)
                total_latency_ms += latency_ms
                timed_out = True
                timeout_count += 1
                error = "timeout"
            except Exception as e:
                latency_ms = int((time.time() - t0) * 1000)
                total_latency_ms += latency_ms
                error = f"request_error:{e.__class__.__name__}:{_norm(e)}"

            raw_rows.append(
                {
                    "review_id": review_id,
                    "request_index": i + 1,
                    "http_status": http_status,
                    "rate_limited": rate_limited,
                    "timeout": timed_out,
                    "parse_method": parse_method,
                    "response_json_parse_success": bool(parsed_obj),
                    "error": error,
                    "usage": usage,
                    "latency_ms": latency_ms,
                    "response_obj": parsed_obj if parsed_obj else {},
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                }
            )

            schema_valid = bool(parsed_obj) and not schema_errors
            logic_valid = bool(logic.get("validation_pass", False))
            validation_pass = schema_valid and logic_valid
            audits.append(
                {
                    "review_id": review_id,
                    "schema_valid": schema_valid,
                    "logic_valid": logic_valid,
                    "validation_pass": validation_pass,
                    "schema_errors": "|".join(schema_errors),
                    "logic_errors": "|".join(logic.get("errors", [])),
                    "hallucinated_value_count": logic["hallucinated_value_count"],
                    "invalid_source_row_reference_count": logic["invalid_source_row_reference_count"],
                    "bad_eps_ratio_count": logic["bad_eps_ratio_count"],
                    "requires_human_approval": bool(parsed_obj.get("requires_human_approval", False)) if parsed_obj else False,
                    "suggested_action": _norm(parsed_obj.get("suggested_action")) if parsed_obj else "",
                    "confidence": parsed_obj.get("confidence", "") if parsed_obj else "",
                }
            )

            if validation_pass:
                validated.append(
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
                rejected.append(
                    {
                        "review_id": review_id,
                        "reason": "validation_failed_or_api_error",
                        "http_status": http_status,
                        "error": error,
                        "schema_errors": "|".join(schema_errors),
                        "logic_errors": "|".join(logic.get("errors", [])),
                    }
                )

            if rate_limited or timed_out:
                stop_reason = "rate_limited" if rate_limited else "timeout"
                break

            if i < len(selected) - 1:
                time.sleep(15)

    _write_jsonl(OUT_RAW, raw_rows)
    _write_excel(OUT_AUDIT, "validation_audit", audits)
    _write_excel(OUT_VALID, "validated_suggestions", validated)
    _write_excel(OUT_REJ, "rejected_suggestions", rejected)

    real_api_response_count = int(sum(1 for r in raw_rows if r.get("response_json_parse_success")))
    schema_valid_response_count = int(sum(1 for a in audits if a.get("schema_valid")))
    schema_invalid_response_count = int(sum(1 for a in audits if not a.get("schema_valid")))
    validated_suggestion_count = int(len(validated))
    rejected_suggestion_count = int(len(rejected))
    requires_human_approval_count = int(sum(1 for a in audits if a.get("requires_human_approval")))
    hallucinated_value_count = int(sum(int(a.get("hallucinated_value_count", 0) or 0) for a in audits))
    invalid_source_row_reference_count = int(sum(int(a.get("invalid_source_row_reference_count", 0) or 0) for a in audits))
    bad_eps_ratio_count = int(sum(int(a.get("bad_eps_ratio_count", 0) or 0) for a in audits))

    _write_json(
        OUT_COST,
        {
            "provider": "openai_compatible",
            "model": _norm(model),
            "selected_review_request_count": len(selected),
            "executed_request_count": len(raw_rows),
            "stop_reason": stop_reason,
            "rate_limited_count": rate_limited_count,
            "timeout_count": timeout_count,
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
            "avg_latency_ms": (total_latency_ms / len(raw_rows)) if raw_rows else 0,
            "total_latency_ms": total_latency_ms,
        },
    )

    after = _snapshot_hashes()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]
    delivery = _run_delivery_check()
    check_status = _norm(delivery.get("overall_status"))

    eps_case_available = bool(fix_summary.get("eps_case_available", False))
    request_pool_missing_categories = fix_summary.get("request_pool_missing_categories", [])

    summary = {
        "stage": "stage7m2_slim_three_case_strict_schema_api_dry_run",
        "mode": "real_api_three_case_slim_strict_schema_sandbox",
        "based_on_stage7m_fix_commit": "54e048f5e68ef0844e0d99a943388df0dc497fad",
        "external_api_called": external_api_called,
        "provider": "openai_compatible",
        "model": _norm(model) or "glm-4.7",
        "selected_review_request_count": len(selected),
        "real_api_response_count": real_api_response_count,
        "schema_valid_response_count": schema_valid_response_count,
        "schema_invalid_response_count": schema_invalid_response_count,
        "validated_suggestion_count": validated_suggestion_count,
        "rejected_suggestion_count": rejected_suggestion_count,
        "requires_human_approval_count": requires_human_approval_count,
        "rate_limited_count": rate_limited_count,
        "timeout_count": timeout_count,
        "hallucinated_value_count": hallucinated_value_count,
        "invalid_source_row_reference_count": invalid_source_row_reference_count,
        "bad_eps_ratio_count": bad_eps_ratio_count,
        "eps_case_available": eps_case_available,
        "request_pool_missing_categories": request_pool_missing_categories,
        "api_key_committed": False,
        "api_key_logged": False,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": check_status,
        "ready_for_stage7n_ai_assisted_review_batch_policy": bool(
            len(selected) == 3
            and len(raw_rows) == 3
            and rate_limited_count == 0
            and timeout_count == 0
            and bad_eps_ratio_count == 0
            and check_status == "PASS"
            and not production_files_modified
            and not official_02b_modified
            and not formal_rules_modified
            and not standardizer_modified
            and not release_package_modified
        ),
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# Stage7M2 Slim Three-case GLM Strict Schema Dry Run",
        "",
        "## Runtime",
        f"- selected_review_request_count: {summary['selected_review_request_count']}",
        f"- executed_request_count: {len(raw_rows)}",
        "- timeout_seconds: 120",
        "- max_tokens: 700",
        "- temperature: 0",
        "- inter_request_interval_seconds: 15",
        f"- stop_reason: {stop_reason if stop_reason else 'none'}",
        "",
        "## Result",
        f"- real_api_response_count: {summary['real_api_response_count']}",
        f"- schema_valid/invalid: {summary['schema_valid_response_count']}/{summary['schema_invalid_response_count']}",
        f"- validated/rejected: {summary['validated_suggestion_count']}/{summary['rejected_suggestion_count']}",
        f"- requires_human_approval_count: {summary['requires_human_approval_count']}",
        f"- rate_limited_count/timeout_count: {summary['rate_limited_count']}/{summary['timeout_count']}",
        f"- hallucinated_value_count: {summary['hallucinated_value_count']}",
        f"- invalid_source_row_reference_count: {summary['invalid_source_row_reference_count']}",
        f"- bad_eps_ratio_count: {summary['bad_eps_ratio_count']}",
        "",
        "## Coverage Facts",
        f"- eps_case_available: {summary['eps_case_available']}",
        f"- request_pool_missing_categories: {summary['request_pool_missing_categories']}",
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
        f"- ready_for_stage7n_ai_assisted_review_batch_policy: {summary['ready_for_stage7n_ai_assisted_review_batch_policy']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

