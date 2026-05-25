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
IN_SLIM_REQ = BASE_DIR / "output" / "stage7m_fix_request_slimming" / "195_stage7m_slim_selected_requests.jsonl"
IN_STAGE7I_REQ = BASE_DIR / "output" / "stage7i_ai_runtime_dry_run" / "188_stage7i_ai_review_requests.jsonl"
IN_SCHEMA = BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_ai_review_response_schema.json"
IN_RULES = BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_ai_validation_rules.json"
IN_STAGE7N_BATCH = BASE_DIR / "output" / "stage7n_batch_new_model_strict_schema_test" / "199_stage7n_batch_new_model_summary.json"

OUT_DIR = BASE_DIR / "output" / "stage7o_five_case_new_model_batch_test"
OUT_SUMMARY = OUT_DIR / "200_stage7o_five_case_summary.json"
OUT_REPORT = OUT_DIR / "200_stage7o_five_case_report.md"
OUT_SELECTED = OUT_DIR / "200_stage7o_selected_requests.jsonl"
OUT_RAW = OUT_DIR / "200_stage7o_raw_responses_sanitized.jsonl"
OUT_AUDIT = OUT_DIR / "200_stage7o_validation_audit.xlsx"
OUT_VALID = OUT_DIR / "200_stage7o_validated_suggestions.xlsx"
OUT_REJ = OUT_DIR / "200_stage7o_rejected_suggestions.xlsx"
OUT_COST = OUT_DIR / "200_stage7o_cost_latency_report.json"

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


def _sanitize_base_url(base_url: str) -> str:
    if not _norm(base_url):
        return ""
    parsed = urlparse(base_url)
    return f"{parsed.scheme or 'https'}://{parsed.hostname or ''}{parsed.path or ''}"


def _is_eps_case(req: Dict[str, Any]) -> bool:
    for r in req.get("candidate_rows", []):
        text = (_norm(r.get("normalized_metric_name")) + " " + _norm(r.get("raw_metric_name"))).lower()
        if "eps" in text or "每股收益" in text:
            return True
    return False


def _metric(req: Dict[str, Any]) -> str:
    if req.get("candidate_rows"):
        r = req["candidate_rows"][0]
        return _norm(r.get("normalized_metric_name")) or _norm(r.get("raw_metric_name"))
    return ""


def _pick_five_requests() -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    slim_rows = _load_jsonl(IN_SLIM_REQ) if IN_SLIM_REQ.exists() else []
    pool_rows = _load_jsonl(IN_STAGE7I_REQ)

    # Prefer slim rows first
    selected: List[Dict[str, Any]] = []
    selected_ids = set()
    selected_metrics = set()
    for r in slim_rows:
        if len(selected) >= 5:
            break
        rid = _norm(r.get("review_id"))
        if rid in selected_ids:
            continue
        selected.append(r)
        selected_ids.add(rid)
        m = _metric(r)
        if m:
            selected_metrics.add(m)

    # Fill from lightweight pool <=5 candidates, prefer metric diversity
    lightweight = [r for r in pool_rows if len(r.get("candidate_rows", [])) <= 5]
    lightweight = sorted(lightweight, key=lambda x: (len(x.get("candidate_rows", [])), _norm(x.get("review_id"))))
    for r in lightweight:
        if len(selected) >= 5:
            break
        rid = _norm(r.get("review_id"))
        if rid in selected_ids:
            continue
        m = _metric(r)
        if m in selected_metrics and len(lightweight) > 5:
            continue
        selected.append(r)
        selected_ids.add(rid)
        if m:
            selected_metrics.add(m)

    # Hard fill if still short
    for r in lightweight:
        if len(selected) >= 5:
            break
        rid = _norm(r.get("review_id"))
        if rid in selected_ids:
            continue
        selected.append(r)
        selected_ids.add(rid)

    reasons = sorted({_norm(r.get("manual_review_reason")) for r in pool_rows})
    has_unit_or_amount_ratio = any(
        _norm(r.get("manual_review_reason")) in {"unit_semantics_uncertain", "amount_vs_ratio_collision"} for r in pool_rows
    )
    eps_available = any(_is_eps_case(r) for r in pool_rows)
    meta = {
        "request_source_priority": "stage7m_slim_then_stage7i_lightweight",
        "pool_size": len(pool_rows),
        "slim_pool_size": len(slim_rows),
        "selected_count": len(selected),
        "selected_metrics": [_metric(r) for r in selected],
        "selected_candidate_rows": [len(r.get("candidate_rows", [])) for r in selected],
        "manual_review_reasons_in_pool": reasons,
        "unit_or_amount_ratio_case_available": has_unit_or_amount_ratio,
        "eps_case_available_in_pool": eps_available,
    }
    return selected[:5], meta


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
        "suggested_unit 必须来自候选或规则允许范围；confidence 为0到1数字；"
        "risk_flags 必须为数组；requires_human_approval 必须为true；"
        "EPS/每股收益不得 ratio；无法判断时使用 keep_manual_review。\n"
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
    bad_eps = 0

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
        sv = _norm(resp.get("suggested_value"))
        su = _norm(resp.get("suggested_unit"))
        if sv and sv not in values:
            hallucinated += 1
            errors.append("hallucinated_value")
        if su and su not in units:
            errors.append("suggested_unit_not_in_candidate")

    metric_text = " ".join(
        [(_norm(r.get("normalized_metric_name")) + " " + _norm(r.get("raw_metric_name"))).lower() for r in req.get("candidate_rows", [])]
    )
    if ("eps" in metric_text or "每股收益" in metric_text) and _norm(resp.get("suggested_unit")) in {"ratio", "%"}:
        bad_eps += 1
        errors.append("eps_ratio_forbidden")

    if not bool(resp.get("requires_human_approval", False)):
        errors.append("requires_human_approval_must_be_true")

    return {
        "errors": errors,
        "validation_pass": len(errors) == 0,
        "hallucinated_value_count": hallucinated,
        "invalid_source_row_reference_count": invalid_ref,
        "bad_eps_ratio_count": bad_eps,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    required = [IN_SCHEMA, IN_RULES, IN_STAGE7N_BATCH]
    for p in required:
        if not p.exists():
            _write_json(
                OUT_SUMMARY,
                {
                    "stage": "stage7o_five_case_new_model_batch_test",
                    "mode": "blocked_missing_input",
                    "external_api_called": False,
                    "blocked_reason": f"missing_input:{p}",
                },
            )
            return 0

    before = _snapshot_hashes()
    schema = _load_json(IN_SCHEMA)
    _rules = _load_json(IN_RULES)
    stage7n_batch_summary = _load_json(IN_STAGE7N_BATCH)
    selected, selection_meta = _pick_five_requests()
    _write_jsonl(OUT_SELECTED, selected)

    api_key = os.environ.get("AI_REVIEW_API_KEY", "")
    base_url = os.environ.get("AI_REVIEW_BASE_URL", "")
    model = os.environ.get("AI_REVIEW_MODEL", "")

    api_key_present = bool(_norm(api_key))
    base_url_sanitized = _sanitize_base_url(base_url)
    timeout_seconds = 90
    max_tokens = 700
    temperature = 0

    external_api_called = False
    raw_rows: List[Dict[str, Any]] = []
    audits: List[Dict[str, Any]] = []
    validated_rows: List[Dict[str, Any]] = []
    rejected_rows: List[Dict[str, Any]] = []
    missing_required_fields_total: List[str] = []
    rate_limited_count = 0
    timeout_count = 0
    latencies: List[float] = []
    total_prompt_tokens = 0
    total_completion_tokens = 0

    if api_key_present and _norm(base_url) and _norm(model):
        external_api_called = True
        endpoint = base_url.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        for idx, req in enumerate(selected):
            review_id = _norm(req.get("review_id"))
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
                if resp.status_code == 429:
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
                    total_prompt_tokens += int(usage.get("prompt_tokens", 0) or 0)
                    total_completion_tokens += int(usage.get("completion_tokens", 0) or 0)
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

            raw_rows.append(
                {
                    "review_id": review_id,
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
                    "schema_valid": schema_valid,
                    "logic_valid": logic_valid,
                    "validation_pass": validation_pass,
                    "schema_errors": "|".join(schema_errors),
                    "logic_errors": "|".join(logic.get("errors", [])),
                    "missing_required_fields": "|".join(missing_fields),
                    "hallucinated_value_count": logic["hallucinated_value_count"],
                    "invalid_source_row_reference_count": logic["invalid_source_row_reference_count"],
                    "bad_eps_ratio_count": logic["bad_eps_ratio_count"],
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
                        "error_type": error_type or "validation_failed",
                        "error_summary": error_summary,
                        "schema_errors": "|".join(schema_errors),
                        "logic_errors": "|".join(logic.get("errors", [])),
                    }
                )

            if idx < len(selected) - 1:
                time.sleep(5)

    _write_jsonl(OUT_RAW, raw_rows)
    _write_excel(OUT_AUDIT, "validation_audit", audits)
    _write_excel(OUT_VALID, "validated_suggestions", validated_rows)
    _write_excel(OUT_REJ, "rejected_suggestions", rejected_rows)

    real_api_response_count = int(sum(1 for r in raw_rows if r.get("response_json_parse_success")))
    schema_valid_response_count = int(sum(1 for a in audits if a.get("schema_valid")))
    schema_invalid_response_count = int(sum(1 for a in audits if not a.get("schema_valid")))
    validated_suggestion_count = int(len(validated_rows))
    rejected_suggestion_count = int(len(rejected_rows))
    requires_human_approval_count = int(sum(1 for a in audits if a.get("requires_human_approval")))
    hallucinated_value_count = int(sum(int(a.get("hallucinated_value_count", 0) or 0) for a in audits))
    invalid_source_row_reference_count = int(sum(int(a.get("invalid_source_row_reference_count", 0) or 0) for a in audits))
    bad_eps_ratio_count = int(sum(int(a.get("bad_eps_ratio_count", 0) or 0) for a in audits))
    eps_case_available = any(_is_eps_case(r) for r in selected)
    avg_latency_seconds = round(sum(latencies) / len(latencies), 3) if latencies else None
    max_latency_seconds = max(latencies) if latencies else None

    _write_json(
        OUT_COST,
        {
            "provider": "openai_compatible",
            "model": _norm(model),
            "selected_review_request_count": len(selected),
            "executed_request_count": len(raw_rows),
            "rate_limited_count": rate_limited_count,
            "timeout_count": timeout_count,
            "avg_latency_seconds": avg_latency_seconds,
            "max_latency_seconds": max_latency_seconds,
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
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

    new_model_five_case_test_pass = bool(
        len(selected) == 5
        and schema_valid_response_count == 5
        and hallucinated_value_count == 0
        and invalid_source_row_reference_count == 0
        and bad_eps_ratio_count == 0
        and timeout_count == 0
        and rate_limited_count == 0
        and requires_human_approval_count == validated_suggestion_count
        and validated_suggestion_count == 5
    )

    if timeout_count > 0:
        failure_reason = "timeout"
    elif rate_limited_count > 0:
        failure_reason = "rate_limit"
    elif schema_valid_response_count < len(selected):
        failure_reason = "schema_invalid"
    elif hallucinated_value_count > 0:
        failure_reason = "hallucinated_value"
    elif invalid_source_row_reference_count > 0:
        failure_reason = "invalid_source_row_reference"
    elif bad_eps_ratio_count > 0:
        failure_reason = "eps_ratio_error"
    else:
        failure_reason = ""

    recommended_next_step = (
        "stage7p_ai_suggestion_queue_integration"
        if new_model_five_case_test_pass
        else f"fix_{failure_reason}_and_retry_stage7o"
    )

    summary = {
        "stage": "stage7o_five_case_new_model_batch_test",
        "mode": "real_api_five_case_new_model_strict_schema",
        "based_on_stage7n_batch_commit": "84cffe155a8f8fb4bb0700bb24049149beb150f0",
        "external_api_called": external_api_called,
        "provider": "openai_compatible",
        "model": _norm(model),
        "base_url_sanitized": base_url_sanitized,
        "api_key_present": api_key_present,
        "api_key_logged": False,
        "selected_review_request_count": len(selected),
        "real_api_response_count": real_api_response_count,
        "schema_valid_response_count": schema_valid_response_count,
        "schema_invalid_response_count": schema_invalid_response_count,
        "missing_required_fields_total": missing_required_fields_total,
        "validated_suggestion_count": validated_suggestion_count,
        "rejected_suggestion_count": rejected_suggestion_count,
        "requires_human_approval_count": requires_human_approval_count,
        "rate_limited_count": rate_limited_count,
        "timeout_count": timeout_count,
        "hallucinated_value_count": hallucinated_value_count,
        "invalid_source_row_reference_count": invalid_source_row_reference_count,
        "bad_eps_ratio_count": bad_eps_ratio_count,
        "eps_case_available": eps_case_available,
        "avg_latency_seconds": avg_latency_seconds,
        "max_latency_seconds": max_latency_seconds,
        "api_key_committed": False,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": check_status,
        "new_model_five_case_test_pass": new_model_five_case_test_pass,
        "failure_reason": failure_reason,
        "recommended_next_step": recommended_next_step,
        "selection_meta": selection_meta,
        "stage7n_batch_pass": bool(stage7n_batch_summary.get("new_model_batch_test_pass", False)),
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# Stage7O Five-case New Model Strict Schema Batch Test",
        "",
        "## Runtime",
        f"- model: {summary['model']}",
        f"- selected_review_request_count: {summary['selected_review_request_count']}",
        "- request_interval_seconds: 5",
        "- timeout_seconds: 90",
        "- max_tokens: 700",
        "- temperature: 0",
        "",
        "## Result",
        f"- real_api_response_count: {summary['real_api_response_count']}",
        f"- schema_valid/invalid: {summary['schema_valid_response_count']}/{summary['schema_invalid_response_count']}",
        f"- missing_required_fields_total: {summary['missing_required_fields_total']}",
        f"- validated/rejected: {summary['validated_suggestion_count']}/{summary['rejected_suggestion_count']}",
        f"- requires_human_approval_count: {summary['requires_human_approval_count']}",
        f"- rate_limited_count/timeout_count: {summary['rate_limited_count']}/{summary['timeout_count']}",
        f"- hallucinated_value_count: {summary['hallucinated_value_count']}",
        f"- invalid_source_row_reference_count: {summary['invalid_source_row_reference_count']}",
        f"- bad_eps_ratio_count: {summary['bad_eps_ratio_count']}",
        f"- eps_case_available: {summary['eps_case_available']}",
        f"- avg_latency_seconds/max_latency_seconds: {summary['avg_latency_seconds']}/{summary['max_latency_seconds']}",
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
        f"- new_model_five_case_test_pass: {summary['new_model_five_case_test_pass']}",
        f"- failure_reason: {summary['failure_reason']}",
        f"- recommended_next_step: {summary['recommended_next_step']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

