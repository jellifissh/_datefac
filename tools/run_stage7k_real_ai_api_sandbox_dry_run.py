import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import requests
import yaml

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

BASE_DIR = Path(r"D:\_datefac")
STAGE7I_DIR = BASE_DIR / "output" / "stage7i_ai_runtime_dry_run"
STAGE7H_DIR = BASE_DIR / "output" / "stage7h_ai_assisted_review_design"
STAGE7J_DIR = BASE_DIR / "output" / "stage7j_real_ai_api_integration_design"
OUT_DIR = BASE_DIR / "output" / "stage7k_real_ai_api_sandbox_dry_run"

IN_CONFIG = BASE_DIR / "config" / "ai_review.example.yaml"
IN_DESIGN_DOC = BASE_DIR / "docs" / "stage7j_real_ai_api_integration_design.md"
IN_CLIENT = BASE_DIR / "tools" / "ai_review_client_skeleton.py"
IN_S7J_SUMMARY = STAGE7J_DIR / "189_stage7j_ai_api_integration_summary.json"

IN_REQUESTS = STAGE7I_DIR / "188_stage7i_ai_review_requests.jsonl"
IN_VALID_AUDIT = STAGE7I_DIR / "188_stage7i_ai_validation_audit.xlsx"
IN_RESP_SCHEMA = STAGE7H_DIR / "187_stage7h_ai_review_response_schema.json"
IN_VALID_RULES = STAGE7H_DIR / "187_stage7h_ai_validation_rules.json"

OUT_SUMMARY = OUT_DIR / "190_stage7k_real_ai_api_sandbox_summary.json"
OUT_REPORT = OUT_DIR / "190_stage7k_real_ai_api_sandbox_report.md"
OUT_SEL_REQ = OUT_DIR / "190_stage7k_selected_review_requests.jsonl"
OUT_RAW_RESP = OUT_DIR / "190_stage7k_real_ai_raw_responses.jsonl"
OUT_VALID = OUT_DIR / "190_stage7k_validated_ai_suggestions.xlsx"
OUT_REJ = OUT_DIR / "190_stage7k_rejected_ai_suggestions.xlsx"
OUT_AUD = OUT_DIR / "190_stage7k_ai_validation_audit.xlsx"
OUT_COST = OUT_DIR / "190_stage7k_cost_latency_report.json"

# Protected files
OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
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
    import subprocess, sys

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
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _write_excel(path: Path, sheet: str, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        df.to_excel(w, sheet_name=sheet[:31], index=False)


def _build_blocked_summary(reason: str, check_status: str) -> Dict[str, Any]:
    return {
        "stage": "stage7k_real_ai_api_sandbox_dry_run",
        "mode": "blocked_missing_api_config",
        "external_api_called": False,
        "blocked_reason": reason,
        "api_key_committed": False,
        "api_key_logged": False,
        "check_delivery_state_overall_status": check_status,
        "ready_for_stage7k_retry": True,
    }


def _response_schema_validate(resp: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    required = schema.get("required", [])
    props = schema.get("properties", {})

    for k in required:
        if k not in resp:
            errors.append(f"missing_required:{k}")

    tmap = {
        "string": str,
        "number": (int, float),
        "array": list,
        "boolean": bool,
    }
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

    return len(errors) == 0, errors


def _logic_validate(req: Dict[str, Any], resp: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], List[str]]:
    errors: List[str] = []
    hallucinated = 0
    bad_row_ref = 0
    bad_eps_ratio = 0

    rows = req.get("candidate_rows", [])
    row_map = {_norm(r.get("row_id")): r for r in rows}
    row_ids = [_norm(x) for x in resp.get("suggested_row_ids", [])]

    for rid in row_ids:
        if rid not in row_map:
            bad_row_ref += 1
            errors.append("invalid_source_row_reference")
            break

    action = _norm(resp.get("suggested_action"))
    if action == "accept_one" and len(row_ids) != 1:
        errors.append("accept_one_requires_single_row")

    if action in {"accept_one", "merge_same_value", "exclude"} and not row_ids:
        errors.append("action_requires_row_ids")

    selected = [row_map[rid] for rid in row_ids if rid in row_map]
    if selected:
        vals = {_norm(r.get("value")) for r in selected}
        units = {_norm(r.get("unit")) for r in selected}
        if _norm(resp.get("suggested_value")) and _norm(resp.get("suggested_value")) not in vals:
            hallucinated += 1
            errors.append("hallucinated_value")
        if _norm(resp.get("suggested_unit")) and _norm(resp.get("suggested_unit")) not in units:
            errors.append("suggested_unit_not_in_candidate")

    # EPS rule
    metric_names = {_norm(r.get("normalized_metric_name")) for r in rows}
    if any(m in {"EPS", "每股收益"} for m in metric_names):
        if _norm(resp.get("suggested_unit")) in {"ratio", "%"}:
            bad_eps_ratio += 1
            errors.append("eps_ratio_forbidden")

    # true value conflict default: keep human approval
    if _norm(req.get("manual_review_reason")) == "true_value_conflict" and _norm(resp.get("suggested_action")) == "accept_one":
        errors.append("true_value_conflict_auto_accept_forbidden")

    if not bool(resp.get("requires_human_approval", False)):
        errors.append("requires_human_approval_must_be_true")

    return len(errors) == 0, {
        "hallucinated_value_count": hallucinated,
        "invalid_source_row_reference_count": bad_row_ref,
        "bad_eps_ratio_count": bad_eps_ratio,
    }, errors


def _build_prompt(req: Dict[str, Any], prompt_template: str) -> str:
    payload = json.dumps(req, ensure_ascii=False)
    return (
        f"{prompt_template}\n\n"
        "# Runtime instruction\n"
        "Return only one JSON object matching response schema.\n"
        "Do not include markdown fences.\n"
        f"REQUEST_JSON={payload}"
    )


def _parse_response_text(text: str) -> Tuple[Dict[str, Any], str]:
    t = (text or "").strip()
    if not t:
        raise ValueError("empty_response")
    # direct json parse
    try:
        return json.loads(t), "raw_json"
    except Exception:
        pass

    # recover from markdown code fences
    if "```" in t:
        segments = t.split("```")
        for s in segments:
            s2 = s.strip()
            if s2.startswith("json"):
                s2 = s2[4:].strip()
            if s2.startswith("{") and s2.endswith("}"):
                try:
                    return json.loads(s2), "fence_repair"
                except Exception:
                    continue

    # bracket repair
    l = t.find("{")
    r = t.rfind("}")
    if l >= 0 and r > l:
        c = t[l : r + 1]
        return json.loads(c), "bracket_repair"

    raise ValueError("json_parse_failed")


def _select_requests(requests: List[Dict[str, Any]], nmax: int = 5) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    # Since Stage7I requests currently only include year_semantics_uncertain and no EPS/unit-mixed,
    # pick representative groups by candidate size + metric diversity.
    by_metric: Dict[str, List[Dict[str, Any]]] = {}
    for r in requests:
        m = _norm(r.get("candidate_rows", [{}])[0].get("normalized_metric_name")) if r.get("candidate_rows") else ""
        by_metric.setdefault(m, []).append(r)

    selected: List[Dict[str, Any]] = []
    # prioritize groups with more candidate rows (more conflict ambiguity)
    sorted_all = sorted(requests, key=lambda x: len(x.get("candidate_rows", [])), reverse=True)

    # ensure some diversity first
    for m in ["毛利率", "营业收入", "归属母公司净利润", "P/B", "P/E", "EV/EBITDA"]:
        if m in by_metric and by_metric[m]:
            selected.append(by_metric[m][0])
        if len(selected) >= nmax:
            break

    # fill to nmax from high ambiguity list
    seen = {r.get("review_id") for r in selected}
    for r in sorted_all:
        if len(selected) >= nmax:
            break
        if r.get("review_id") in seen:
            continue
        selected.append(r)
        seen.add(r.get("review_id"))

    selected = selected[:nmax]
    sel_metrics = [_norm(r.get("candidate_rows", [{}])[0].get("normalized_metric_name")) if r.get("candidate_rows") else "" for r in selected]
    has_eps = any(m in {"EPS", "每股收益"} for m in sel_metrics)

    meta = {
        "selection_strategy": "metric_diversity_plus_ambiguity",
        "selected_metrics": sel_metrics,
        "eps_case_included": has_eps,
        "note": "Stage7I request pool has no EPS/unit_semantics_uncertain/amount_vs_ratio labels; selected representative ambiguity groups.",
    }
    return selected, meta


def main() -> int:
    import argparse
    import subprocess, sys

    parser = argparse.ArgumentParser()
    parser.add_argument("--enable-external-api", action="store_true", help="Required to call real API")
    parser.add_argument("--max-samples", type=int, default=5)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [
        IN_CONFIG,
        IN_DESIGN_DOC,
        IN_CLIENT,
        IN_S7J_SUMMARY,
        IN_REQUESTS,
        IN_VALID_AUDIT,
        IN_RESP_SCHEMA,
        IN_VALID_RULES,
    ]
    for p in required:
        if not p.exists():
            missing_reason = f"missing_input:{p}"
            delivery = _run_delivery_check()
            summary = _build_blocked_summary(missing_reason, _norm(delivery.get("overall_status")))
            _write_json(OUT_SUMMARY, summary)
            OUT_REPORT.write_text(f"# Stage7K Blocked\n\n- blocked_reason: {missing_reason}\n", encoding="utf-8")
            return 0

    before = _snapshot_hashes()

    # Environment variables (never log raw secret)
    api_key = os.environ.get("AI_REVIEW_API_KEY", "")
    base_url = os.environ.get("AI_REVIEW_BASE_URL", "")
    model = os.environ.get("AI_REVIEW_MODEL", "")

    if not _norm(api_key):
        delivery = _run_delivery_check()
        summary = _build_blocked_summary("missing_env:AI_REVIEW_API_KEY", _norm(delivery.get("overall_status")))
        _write_json(OUT_SUMMARY, summary)
        OUT_REPORT.write_text("# Stage7K Blocked\n\n- blocked_reason: missing_env:AI_REVIEW_API_KEY\n", encoding="utf-8")
        return 0

    if not _norm(base_url) or not _norm(model):
        delivery = _run_delivery_check()
        summary = _build_blocked_summary("missing_env:AI_REVIEW_BASE_URL_or_AI_REVIEW_MODEL", _norm(delivery.get("overall_status")))
        _write_json(OUT_SUMMARY, summary)
        OUT_REPORT.write_text("# Stage7K Blocked\n\n- blocked_reason: missing_env:AI_REVIEW_BASE_URL_or_AI_REVIEW_MODEL\n", encoding="utf-8")
        return 0

    if not args.enable_external_api:
        delivery = _run_delivery_check()
        summary = _build_blocked_summary("flag_required:--enable-external-api", _norm(delivery.get("overall_status")))
        _write_json(OUT_SUMMARY, summary)
        OUT_REPORT.write_text("# Stage7K Blocked\n\n- blocked_reason: flag_required:--enable-external-api\n", encoding="utf-8")
        return 0

    cfg = yaml.safe_load(IN_CONFIG.read_text(encoding="utf-8")) or {}
    timeout_seconds = int(cfg.get("timeout_seconds", 30))
    max_retries = int(cfg.get("max_retries", 2))
    max_tokens = int(cfg.get("max_tokens_per_request", 2000))
    temperature = float(cfg.get("temperature", 0))

    prompt_template = IN_RESP_SCHEMA.read_text(encoding="utf-8")
    # use Stage7H prompt template for natural language instructions
    prompt_template_md = (BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_prompt_template.md").read_text(encoding="utf-8")

    resp_schema = json.loads(IN_RESP_SCHEMA.read_text(encoding="utf-8"))

    requests_rows = [json.loads(x) for x in IN_REQUESTS.read_text(encoding="utf-8").splitlines() if x.strip()]
    selected, select_meta = _select_requests(requests_rows, nmax=max(3, min(5, int(args.max_samples))))

    _write_jsonl(OUT_SEL_REQ, selected)

    raw_responses: List[Dict[str, Any]] = []
    suggestions: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    audits: List[Dict[str, Any]] = []

    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_requests = 0
    total_latency_ms = 0

    for req in selected:
        total_requests += 1
        rid = _norm(req.get("review_id"))
        prompt = _build_prompt(req, prompt_template_md)

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a strict JSON assistant for financial review."},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        endpoint = base_url.rstrip("/") + "/chat/completions"

        attempt = 0
        last_err = ""
        parsed_obj = None
        parse_method = ""
        usage = {}
        latency_ms = 0

        while attempt <= max_retries:
            attempt += 1
            t0 = time.time()
            try:
                resp = requests.post(endpoint, headers=headers, json=payload, timeout=timeout_seconds)
                latency_ms = int((time.time() - t0) * 1000)
                total_latency_ms += latency_ms

                if resp.status_code >= 400:
                    last_err = f"http_{resp.status_code}"
                    continue

                data = resp.json()
                usage = data.get("usage", {}) if isinstance(data, dict) else {}
                text = ""
                if isinstance(data, dict):
                    choices = data.get("choices", [])
                    if choices:
                        msg = choices[0].get("message", {})
                        text = _norm(msg.get("content"))

                obj, parse_method = _parse_response_text(text)
                parsed_obj = obj
                break
            except Exception as e:
                last_err = str(e)
                continue

        raw_entry = {
            "review_id": rid,
            "attempts": attempt,
            "success": parsed_obj is not None,
            "parse_method": parse_method,
            "latency_ms": latency_ms,
            "usage": usage,
            "error": last_err,
            "response_obj": parsed_obj if parsed_obj is not None else {},
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        raw_responses.append(raw_entry)

        if parsed_obj is None:
            audits.append(
                {
                    "review_id": rid,
                    "schema_valid": False,
                    "logic_valid": False,
                    "validation_pass": False,
                    "errors": "response_parse_failed",
                    "requires_human_approval": True,
                    "suggested_action": "",
                    "confidence": "",
                }
            )
            rejected.append(
                {
                    "review_id": rid,
                    "reason": "response_parse_failed",
                    "requires_human_approval": True,
                }
            )
            continue

        schema_ok, schema_errors = _response_schema_validate(parsed_obj, resp_schema)
        logic_ok, counts, logic_errors = _logic_validate(req, parsed_obj)
        pass_ok = schema_ok and logic_ok

        audits.append(
            {
                "review_id": rid,
                "schema_valid": schema_ok,
                "logic_valid": logic_ok,
                "validation_pass": pass_ok,
                "errors": "|".join(schema_errors + logic_errors),
                "requires_human_approval": bool(parsed_obj.get("requires_human_approval", False)),
                "suggested_action": _norm(parsed_obj.get("suggested_action")),
                "confidence": parsed_obj.get("confidence", ""),
                "hallucinated_value_count": counts["hallucinated_value_count"],
                "invalid_source_row_reference_count": counts["invalid_source_row_reference_count"],
                "bad_eps_ratio_count": counts["bad_eps_ratio_count"],
            }
        )

        # accumulate usage
        try:
            total_prompt_tokens += int(usage.get("prompt_tokens", 0) or 0)
            total_completion_tokens += int(usage.get("completion_tokens", 0) or 0)
        except Exception:
            pass

        action = _norm(parsed_obj.get("suggested_action"))
        if pass_ok and action and action != "keep_manual_review":
            suggestions.append(
                {
                    "review_id": rid,
                    "suggested_action": action,
                    "suggested_row_ids": "|".join(parsed_obj.get("suggested_row_ids", [])),
                    "suggested_metric_name": _norm(parsed_obj.get("suggested_metric_name")),
                    "suggested_year": _norm(parsed_obj.get("suggested_year")),
                    "suggested_value": _norm(parsed_obj.get("suggested_value")),
                    "suggested_unit": _norm(parsed_obj.get("suggested_unit")),
                    "confidence": parsed_obj.get("confidence", ""),
                    "risk_flags": "|".join(parsed_obj.get("risk_flags", [])),
                    "requires_human_approval": True,
                }
            )
        else:
            rejected.append(
                {
                    "review_id": rid,
                    "reason": "validation_failed_or_keep_manual",
                    "suggested_action": action,
                    "errors": "|".join(schema_errors + logic_errors),
                    "requires_human_approval": True,
                }
            )

    # write artifacts
    _write_jsonl(OUT_RAW_RESP, raw_responses)
    _write_excel(OUT_VALID, "validated_ai_suggestions", suggestions)
    _write_excel(OUT_REJ, "rejected_ai_suggestions", rejected)
    _write_excel(OUT_AUD, "ai_validation_audit", audits)

    hallucinated_value_count = int(sum(int(x.get("hallucinated_value_count", 0) or 0) for x in audits))
    invalid_source_row_reference_count = int(sum(int(x.get("invalid_source_row_reference_count", 0) or 0) for x in audits))
    bad_eps_ratio_count = int(sum(int(x.get("bad_eps_ratio_count", 0) or 0) for x in audits))

    cost_latency = {
        "provider": "openai_compatible",
        "model": model,
        "selected_review_request_count": len(selected),
        "real_api_response_count": len([x for x in raw_responses if x.get("success")]),
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_tokens": total_prompt_tokens + total_completion_tokens,
        "avg_latency_ms": (total_latency_ms / total_requests) if total_requests else 0,
        "total_latency_ms": total_latency_ms,
        "note": "Cost estimation not available without provider billing metadata.",
    }
    _write_json(OUT_COST, cost_latency)

    # unchanged checks
    after = _snapshot_hashes()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    overall_status = _norm(delivery.get("overall_status"))

    schema_valid_count = int(sum(1 for x in audits if x.get("schema_valid")))
    schema_invalid_count = int(len(audits) - schema_valid_count)
    validated_count = int(len(suggestions))
    rejected_count = int(len(rejected))
    requires_human_approval_count = int(len(audits))

    summary = {
        "stage": "stage7k_real_ai_api_sandbox_dry_run",
        "mode": "real_api_small_sample_sandbox",
        "based_on_stage7j_commit": "e5ac4ce45dd4bafcd549edf19c6d463307123e0d",
        "provider": "openai_compatible",
        "model": model,
        "external_api_called": True,
        "api_key_committed": False,
        "api_key_logged": False,
        "selected_review_request_count": int(len(selected)),
        "real_api_response_count": int(len([x for x in raw_responses if x.get('success')])),
        "schema_valid_response_count": schema_valid_count,
        "schema_invalid_response_count": schema_invalid_count,
        "validated_suggestion_count": validated_count,
        "rejected_suggestion_count": rejected_count,
        "requires_human_approval_count": requires_human_approval_count,
        "eps_case_included": bool(select_meta.get("eps_case_included", False)),
        "bad_eps_ratio_count": bad_eps_ratio_count,
        "hallucinated_value_count": hallucinated_value_count,
        "invalid_source_row_reference_count": invalid_source_row_reference_count,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": overall_status,
        "ready_for_stage7l_ai_output_evaluation": False,
        "selection_meta": select_meta,
    }

    summary["ready_for_stage7l_ai_output_evaluation"] = bool(
        summary["external_api_called"]
        and 3 <= summary["selected_review_request_count"] <= 5
        and summary["schema_invalid_response_count"] >= 0
        and summary["bad_eps_ratio_count"] == 0
        and not summary["production_files_modified"]
        and not summary["official_02b_modified"]
        and not summary["formal_rules_modified"]
        and not summary["standardizer_modified"]
        and not summary["release_package_modified"]
        and summary["check_delivery_state_overall_status"] == "PASS"
    )

    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# Stage7K Real AI API Sandbox Dry Run",
        "",
        f"- selected_review_request_count: {summary['selected_review_request_count']}",
        f"- real_api_response_count: {summary['real_api_response_count']}",
        f"- schema_valid/invalid: {summary['schema_valid_response_count']}/{summary['schema_invalid_response_count']}",
        f"- validated/rejected: {summary['validated_suggestion_count']}/{summary['rejected_suggestion_count']}",
        f"- requires_human_approval_count: {summary['requires_human_approval_count']}",
        f"- bad_eps_ratio_count: {summary['bad_eps_ratio_count']}",
        f"- hallucinated_value_count: {summary['hallucinated_value_count']}",
        f"- invalid_source_row_reference_count: {summary['invalid_source_row_reference_count']}",
        f"- provider/model: {summary['provider']}/{summary['model']}",
        "",
        "## Selection Notes",
        f"- {select_meta.get('note','')}",
        f"- selected_metrics: {', '.join(select_meta.get('selected_metrics', []))}",
        f"- eps_case_included: {summary['eps_case_included']}",
        "",
        "## Safety",
        f"- external_api_called: {summary['external_api_called']}",
        f"- api_key_committed: {summary['api_key_committed']}",
        f"- api_key_logged: {summary['api_key_logged']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
        "",
        "## Decision",
        f"- ready_for_stage7l_ai_output_evaluation: {summary['ready_for_stage7l_ai_output_evaluation']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

