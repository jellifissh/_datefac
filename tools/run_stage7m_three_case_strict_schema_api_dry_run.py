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
IN_REQUESTS = BASE_DIR / "output" / "stage7i_ai_runtime_dry_run" / "188_stage7i_ai_review_requests.jsonl"
IN_SCHEMA = BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_ai_review_response_schema.json"
IN_RULES = BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_ai_validation_rules.json"
IN_STAGE7L_SUMMARY = BASE_DIR / "output" / "stage7l_ai_output_evaluation" / "193_stage7l_ai_output_evaluation_summary.json"

OUT_DIR = BASE_DIR / "output" / "stage7m_three_case_strict_schema_api_dry_run"
OUT_SUMMARY = OUT_DIR / "194_stage7m_three_case_summary.json"
OUT_REPORT = OUT_DIR / "194_stage7m_three_case_report.md"
OUT_SELECTED = OUT_DIR / "194_stage7m_selected_requests.jsonl"
OUT_RAW = OUT_DIR / "194_stage7m_raw_responses_sanitized.jsonl"
OUT_AUDIT = OUT_DIR / "194_stage7m_validation_audit.xlsx"
OUT_VALID = OUT_DIR / "194_stage7m_validated_suggestions.xlsx"
OUT_REJ = OUT_DIR / "194_stage7m_rejected_suggestions.xlsx"
OUT_COST = OUT_DIR / "194_stage7m_cost_latency_report.json"

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


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_excel(path: Path, sheet: str, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        df.to_excel(w, sheet_name=sheet[:31], index=False)


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

    payload = {
        "review_id": _norm(req.get("review_id")),
        "conflict_reason": _norm(req.get("manual_review_reason")),
        "candidate_rows": compact_rows,
        "known_rules": {"eps_unit_forbidden_ratio": True},
    }

    return (
        "你是严格 JSON 输出器。只输出一个 JSON object，不要 markdown，不要其他文字。\n"
        "必须包含全部字段："
        + ", ".join(required_fields)
        + "\n"
        "要求：suggested_row_ids 必须来自 candidate_rows；suggested_value 不得编造；"
        "risk_flags 必须是数组；confidence 必须在0到1；requires_human_approval 必须为 true；"
        "无法判断时 suggested_action=keep_manual_review。\n"
        "返回模板（字段不可缺失）："
        + json.dumps(strict_template, ensure_ascii=False)
        + "\n输入："
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
    tmap = {"string": str, "number": (int, float), "array": list, "boolean": bool}
    for key, conf in props.items():
        if key not in resp_obj:
            continue
        et = conf.get("type")
        if et in tmap and not isinstance(resp_obj[key], tmap[et]):
            errs.append(f"type_mismatch:{key}:{et}")
    enum = props.get("suggested_action", {}).get("enum", [])
    if enum and _norm(resp_obj.get("suggested_action")) not in set(enum):
        errs.append("suggested_action_enum_invalid")
    try:
        c = float(resp_obj.get("confidence"))
        if c < 0 or c > 1:
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
    selected_ids = [_norm(x) for x in resp_obj.get("suggested_row_ids", [])]
    action = _norm(resp_obj.get("suggested_action"))

    for rid in selected_ids:
        if rid not in row_map:
            invalid_ref += 1
            errs.append("invalid_source_row_reference")
            break

    if action == "accept_one" and len(selected_ids) != 1:
        errs.append("accept_one_requires_single_row")
    if action in {"accept_one", "merge_same_value", "exclude"} and not selected_ids:
        errs.append("action_requires_row_ids")

    selected_rows = [row_map[rid] for rid in selected_ids if rid in row_map]
    if selected_rows:
        values = {_norm(r.get("value")) for r in selected_rows}
        units = {_norm(r.get("unit")) for r in selected_rows}
        sv = _norm(resp_obj.get("suggested_value"))
        su = _norm(resp_obj.get("suggested_unit"))
        if sv and sv not in values:
            hallucinated += 1
            errs.append("hallucinated_value")
        if su and su not in units:
            errs.append("suggested_unit_not_in_candidate")

    metric_text = " ".join(
        [(_norm(r.get("normalized_metric_name")) + " " + _norm(r.get("raw_metric_name"))).lower() for r in req.get("candidate_rows", [])]
    )
    if ("eps" in metric_text or "每股收益" in metric_text) and _norm(resp_obj.get("suggested_unit")) in {"ratio", "%"}:
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


def _is_eps_case(req: Dict[str, Any]) -> bool:
    for r in req.get("candidate_rows", []):
        text = (_norm(r.get("normalized_metric_name")) + " " + _norm(r.get("raw_metric_name"))).lower()
        if "eps" in text or "每股收益" in text:
            return True
    return False


def _select_three_requests(all_rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    reasons = {}
    for r in all_rows:
        reason = _norm(r.get("manual_review_reason"))
        reasons[reason] = reasons.get(reason, 0) + 1

    target_reasons = ["true_value_conflict", "unit_semantics_uncertain", "amount_vs_ratio_collision"]
    reason_to_rows: Dict[str, List[Dict[str, Any]]] = {}
    for r in all_rows:
        reason_to_rows.setdefault(_norm(r.get("manual_review_reason")), []).append(r)

    selected: List[Dict[str, Any]] = []
    requested_available = {}
    for tr in target_reasons:
        candidates = reason_to_rows.get(tr, [])
        requested_available[tr] = len(candidates)
        if candidates:
            selected.append(candidates[0])

    # fill remaining slots by highest ambiguity + metric diversity
    if len(selected) < 3:
        selected_ids = {_norm(x.get("review_id")) for x in selected}
        sorted_rows = sorted(all_rows, key=lambda x: len(x.get("candidate_rows", [])), reverse=True)
        used_metrics = set()
        for r in selected:
            first = r.get("candidate_rows", [{}])[0]
            used_metrics.add(_norm(first.get("normalized_metric_name")))

        for r in sorted_rows:
            if len(selected) >= 3:
                break
            rid = _norm(r.get("review_id"))
            if rid in selected_ids:
                continue
            metric = _norm(r.get("candidate_rows", [{}])[0].get("normalized_metric_name"))
            if metric and metric in used_metrics and len(sorted_rows) > 3:
                continue
            selected.append(r)
            selected_ids.add(rid)
            used_metrics.add(metric)

        # hard fill if still short
        for r in sorted_rows:
            if len(selected) >= 3:
                break
            rid = _norm(r.get("review_id"))
            if rid in selected_ids:
                continue
            selected.append(r)
            selected_ids.add(rid)

    selected = selected[:3]
    has_eps = any(_is_eps_case(r) for r in selected)
    meta = {
        "input_request_count": len(all_rows),
        "manual_review_reason_distribution": reasons,
        "requested_reason_available_counts": requested_available,
        "requested_reason_constraints_fully_met": all(requested_available[x] > 0 for x in target_reasons),
        "eps_case_available_count": sum(1 for r in all_rows if _is_eps_case(r)),
        "eps_case_included": has_eps,
        "selection_note": (
            "No true_value_conflict/unit_semantics_uncertain/amount_vs_ratio_collision in Stage7I pool; "
            "selected 3 representative ambiguity groups."
        ),
    }
    return selected, meta


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--enable-external-api", action="store_true")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    required = [IN_REQUESTS, IN_SCHEMA, IN_RULES, IN_STAGE7L_SUMMARY]
    for p in required:
        if not p.exists():
            _write_json(
                OUT_SUMMARY,
                {
                    "stage": "stage7m_three_case_strict_schema_api_dry_run",
                    "mode": "blocked_missing_input",
                    "external_api_called": False,
                    "blocked_reason": f"missing_input:{p}",
                },
            )
            return 0

    before = _snapshot_hashes()
    stage7l_summary = json.loads(IN_STAGE7L_SUMMARY.read_text(encoding="utf-8"))

    api_key = os.environ.get("AI_REVIEW_API_KEY", "")
    base_url = os.environ.get("AI_REVIEW_BASE_URL", "")
    model = os.environ.get("AI_REVIEW_MODEL", "")

    rows = [json.loads(line) for line in IN_REQUESTS.read_text(encoding="utf-8").splitlines() if line.strip()]
    schema = json.loads(IN_SCHEMA.read_text(encoding="utf-8"))
    selected, selection_meta = _select_three_requests(rows)
    _write_jsonl(OUT_SELECTED, selected)

    if not args.enable_external_api or not _norm(api_key) or not _norm(base_url) or not _norm(model):
        delivery = _run_delivery_check()
        summary = {
            "stage": "stage7m_three_case_strict_schema_api_dry_run",
            "mode": "blocked_missing_api_config",
            "based_on_stage7l_commit": "c53cd037fb918ce15cda26795731f4bdaea5c46b",
            "external_api_called": False,
            "provider": "openai_compatible",
            "model": _norm(model) or "glm-4.7",
            "selected_review_request_count": len(selected),
            "real_api_response_count": 0,
            "schema_valid_response_count": 0,
            "schema_invalid_response_count": 0,
            "validated_suggestion_count": 0,
            "rejected_suggestion_count": 0,
            "requires_human_approval_count": 0,
            "rate_limited_count": 0,
            "timeout_count": 0,
            "hallucinated_value_count": 0,
            "invalid_source_row_reference_count": 0,
            "bad_eps_ratio_count": 0,
            "api_key_committed": False,
            "api_key_logged": False,
            "production_files_modified": False,
            "official_02b_modified": False,
            "formal_rules_modified": False,
            "standardizer_modified": False,
            "release_package_modified": False,
            "check_delivery_state_overall_status": _norm(delivery.get("overall_status")),
            "ready_for_stage7n_ai_assisted_review_batch_policy": False,
            "selection_meta": selection_meta,
        }
        _write_json(OUT_SUMMARY, summary)
        return 0

    timeout_seconds = 90
    max_tokens = 1000
    temperature = 0
    endpoint = base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    raw_rows: List[Dict[str, Any]] = []
    audits: List[Dict[str, Any]] = []
    valid_rows: List[Dict[str, Any]] = []
    rej_rows: List[Dict[str, Any]] = []

    rate_limited_count = 0
    timeout_count = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_latency_ms = 0
    external_api_called = True
    stop_early = False

    for idx, req in enumerate(selected):
        review_id = _norm(req.get("review_id"))
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

        t0 = time.time()
        http_status = None
        parse_method = ""
        parsed_obj: Dict[str, Any] = {}
        schema_errors: List[str] = []
        logic_result = {
            "errors": ["response_not_available"],
            "validation_pass": False,
            "hallucinated_value_count": 0,
            "invalid_source_row_reference_count": 0,
            "bad_eps_ratio_count": 0,
        }
        rate_limited = False
        timed_out = False
        error = ""
        usage: Dict[str, Any] = {}

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
                msg_content = ""
                if isinstance(data, dict):
                    choices = data.get("choices", [])
                    if choices:
                        msg_content = _norm(choices[0].get("message", {}).get("content"))
                parsed_obj, parse_method = _parse_json_content(msg_content)
                schema_errors = _schema_validate(parsed_obj, schema)
                if not schema_errors:
                    logic_result = _logic_validate(req, parsed_obj)
                else:
                    logic_result = {
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

        row_entry = {
            "review_id": review_id,
            "request_index": idx + 1,
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
        raw_rows.append(row_entry)

        schema_valid = bool(parsed_obj) and len(schema_errors) == 0
        logic_valid = bool(logic_result.get("validation_pass", False))
        validation_pass = schema_valid and logic_valid

        audits.append(
            {
                "review_id": review_id,
                "schema_valid": schema_valid,
                "logic_valid": logic_valid,
                "validation_pass": validation_pass,
                "schema_errors": "|".join(schema_errors),
                "logic_errors": "|".join(logic_result.get("errors", [])),
                "hallucinated_value_count": logic_result["hallucinated_value_count"],
                "invalid_source_row_reference_count": logic_result["invalid_source_row_reference_count"],
                "bad_eps_ratio_count": logic_result["bad_eps_ratio_count"],
                "requires_human_approval": bool(parsed_obj.get("requires_human_approval", False)) if parsed_obj else False,
                "suggested_action": _norm(parsed_obj.get("suggested_action")) if parsed_obj else "",
                "confidence": parsed_obj.get("confidence", "") if parsed_obj else "",
            }
        )

        if validation_pass:
            valid_rows.append(
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
            rej_rows.append(
                {
                    "review_id": review_id,
                    "reason": "validation_failed_or_api_error",
                    "http_status": http_status,
                    "error": error,
                    "schema_errors": "|".join(schema_errors),
                    "logic_errors": "|".join(logic_result.get("errors", [])),
                }
            )

        if rate_limited or timed_out:
            stop_early = True
            break

        if idx < len(selected) - 1:
            time.sleep(10)

    _write_jsonl(OUT_RAW, raw_rows)
    _write_excel(OUT_AUDIT, "validation_audit", audits)
    _write_excel(OUT_VALID, "validated_suggestions", valid_rows)
    _write_excel(OUT_REJ, "rejected_suggestions", rej_rows)

    real_api_response_count = int(sum(1 for r in raw_rows if r.get("response_json_parse_success")))
    schema_valid_count = int(sum(1 for a in audits if a.get("schema_valid")))
    schema_invalid_count = int(sum(1 for a in audits if not a.get("schema_valid")))
    validated_count = int(len(valid_rows))
    rejected_count = int(len(rej_rows))
    requires_human_approval_count = int(sum(1 for a in audits if a.get("requires_human_approval")))
    hallucinated_count = int(sum(int(a.get("hallucinated_value_count", 0) or 0) for a in audits))
    invalid_ref_count = int(sum(int(a.get("invalid_source_row_reference_count", 0) or 0) for a in audits))
    bad_eps_ratio_count = int(sum(int(a.get("bad_eps_ratio_count", 0) or 0) for a in audits))

    _write_json(
        OUT_COST,
        {
            "provider": "openai_compatible",
            "model": model,
            "selected_review_request_count": len(selected),
            "executed_request_count": len(raw_rows),
            "stopped_early_due_to_rate_limit_or_timeout": stop_early,
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
    overall_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "stage7m_three_case_strict_schema_api_dry_run",
        "mode": "real_api_three_case_strict_schema_sandbox",
        "based_on_stage7l_commit": "c53cd037fb918ce15cda26795731f4bdaea5c46b",
        "external_api_called": external_api_called,
        "provider": "openai_compatible",
        "model": model,
        "selected_review_request_count": len(selected),
        "real_api_response_count": real_api_response_count,
        "schema_valid_response_count": schema_valid_count,
        "schema_invalid_response_count": schema_invalid_count,
        "validated_suggestion_count": validated_count,
        "rejected_suggestion_count": rejected_count,
        "requires_human_approval_count": requires_human_approval_count,
        "rate_limited_count": rate_limited_count,
        "timeout_count": timeout_count,
        "hallucinated_value_count": hallucinated_count,
        "invalid_source_row_reference_count": invalid_ref_count,
        "bad_eps_ratio_count": bad_eps_ratio_count,
        "api_key_committed": False,
        "api_key_logged": False,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": overall_status,
        "ready_for_stage7n_ai_assisted_review_batch_policy": bool(
            len(selected) == 3
            and len(raw_rows) == 3
            and rate_limited_count == 0
            and timeout_count == 0
            and bad_eps_ratio_count == 0
            and overall_status == "PASS"
            and not production_files_modified
            and not official_02b_modified
            and not formal_rules_modified
            and not standardizer_modified
            and not release_package_modified
        ),
        "selection_meta": selection_meta,
        "stage7l_recommended_next_stage": _norm(stage7l_summary.get("recommended_next_stage")),
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# Stage7M Three-case Strict Schema GLM API Dry Run",
        "",
        "## Setup",
        f"- selected_review_request_count: {summary['selected_review_request_count']}",
        f"- executed_request_count: {len(raw_rows)}",
        f"- provider/model: {summary['provider']}/{summary['model']}",
        "- timeout_seconds: 90",
        "- max_tokens: 1000",
        "- temperature: 0",
        "- inter_request_sleep_seconds: 10",
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
        "## Selection Constraints",
        f"- requested_reason_constraints_fully_met: {selection_meta.get('requested_reason_constraints_fully_met')}",
        f"- requested_reason_available_counts: {selection_meta.get('requested_reason_available_counts')}",
        f"- eps_case_available_count: {selection_meta.get('eps_case_available_count')}",
        f"- eps_case_included: {selection_meta.get('eps_case_included')}",
        f"- selection_note: {selection_meta.get('selection_note')}",
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

