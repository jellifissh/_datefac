import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Tuple

import requests

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

BASE_DIR = Path(r"D:\_datefac")
OUT_DIR = BASE_DIR / "output" / "stage7k_fix_ai_connectivity_diagnosis"
OUT_SUMMARY = OUT_DIR / "191_stage7k_fix_ai_connectivity_summary.json"
OUT_REPORT = OUT_DIR / "191_stage7k_fix_ai_connectivity_report.md"
OUT_LOG = OUT_DIR / "191_stage7k_fix_connection_test_log.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"


# 1 lightweight test call only
MAX_TEST_CALLS = 1


def _norm(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _snapshot() -> Dict[str, str]:
    snap = s5k._snapshot_hashes()
    snap["official_02b"] = _sha256(OFFICIAL_02B)
    snap["formal_rules"] = _sha256(FORMAL_SCOPE_RULES)
    snap["standardizer"] = _sha256(STANDARDIZER_FILE)
    snap["release_zip"] = _sha256(RELEASE_ZIP)
    return snap


def _delivery_status() -> str:
    import subprocess

    p = subprocess.run(
        [sys.executable, str(BASE_DIR / "tools" / "check_delivery_state.py"), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    txt = (p.stdout or "").strip()
    if not txt:
        return "UNKNOWN"
    try:
        return _norm(json.loads(txt).get("overall_status"))
    except Exception:
        return "UNKNOWN"


def _classify_error(http_status: int, err_text: str) -> Tuple[str, str]:
    t = (err_text or "").lower()

    if http_status:
        if http_status == 401:
            return "HTTP_401", "Check API key validity and provider auth settings."
        if http_status == 403:
            return "HTTP_403", "Check account permission / IP whitelist / provider policy."
        if http_status == 404:
            return "HTTP_404", "Check base_url and endpoint path compatibility (likely /chat/completions path mismatch)."
        if http_status == 429:
            return "HTTP_429", "Hit rate limit; reduce request frequency or upgrade quota."
        if 400 <= http_status < 500:
            return "HTTP_4XX", "Client request rejected; verify payload and provider compatibility."
        if http_status >= 500:
            return "HTTP_5XX", "Provider server error; retry later or switch endpoint."

    if "name or service not known" in t or "getaddrinfo" in t or "dns" in t:
        return "DNS_ERROR", "Check DNS resolution and base_url host correctness."
    if "timed out" in t or "timeout" in t:
        return "CONNECTION_TIMEOUT", "Check outbound network and increase timeout if needed."
    if "ssl" in t or "tls" in t or "certificate" in t:
        return "TLS_SSL_ERROR", "Check TLS certificates and HTTPS interception/proxy settings."
    if "proxy" in t:
        return "PROXY_ERROR", "Check proxy settings or bypass for provider domain."
    if "connection" in t or "failed to establish a new connection" in t or "winerror 10013" in t:
        return "CONNECTION_ERROR", "Outbound socket blocked; check firewall/endpoint protection/network policy for provider domain:443."
    if "json" in t or "parse" in t:
        return "RESPONSE_FORMAT_ERROR", "Provider returned non-JSON or incompatible format; enforce strict JSON response mode."

    return "OTHER", "Inspect raw error and provider compatibility details."


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    before = _snapshot()

    # env presence only, do not log actual values
    api_key = os.environ.get("AI_REVIEW_API_KEY", "")
    base_url = os.environ.get("AI_REVIEW_BASE_URL", "")
    model = os.environ.get("AI_REVIEW_MODEL", "")

    api_key_present = bool(_norm(api_key))
    base_url_present = bool(_norm(base_url))
    model_present = bool(_norm(model))

    external_api_test_attempted = False
    external_api_test_success = False
    http_status = None
    error_type = ""
    error_summary = ""
    recommended_fix = ""

    test_log: Dict[str, Any] = {
        "provider": "openai_compatible",
        "model": _norm(model) if model_present else "",
        "api_key_present": api_key_present,
        "api_key_logged": False,
        "base_url_present": base_url_present,
        "model_present": model_present,
        "test_call_count": 0,
        "max_test_calls": MAX_TEST_CALLS,
        "endpoint_tested": "",
        "http_status": None,
        "error_type": "",
        "error_summary": "",
        "latency_ms": 0,
    }

    if api_key_present and base_url_present and model_present:
        external_api_test_attempted = True
        endpoint = _norm(base_url).rstrip("/") + "/chat/completions"
        test_log["endpoint_tested"] = endpoint

        payload = {
            "model": _norm(model),
            "messages": [
                {"role": "system", "content": "Return strict JSON object only."},
                {"role": "user", "content": '{"ping":"pong"}'},
            ],
            "temperature": 0,
            "max_tokens": 16,
            "response_format": {"type": "json_object"},
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        t0 = time.time()
        test_log["test_call_count"] = 1
        try:
            resp = requests.post(endpoint, headers=headers, json=payload, timeout=15)
            test_log["latency_ms"] = int((time.time() - t0) * 1000)
            http_status = int(resp.status_code)
            test_log["http_status"] = http_status

            if 200 <= http_status < 300:
                # basic format check
                try:
                    _ = resp.json()
                    external_api_test_success = True
                    error_type = ""
                    error_summary = ""
                    recommended_fix = ""
                except Exception as e:
                    external_api_test_success = False
                    error_type, recommended_fix = _classify_error(http_status, str(e))
                    error_summary = "response_json_parse_failed"
            else:
                external_api_test_success = False
                body = resp.text[:500]
                error_type, recommended_fix = _classify_error(http_status, body)
                error_summary = f"http_error_{http_status}"
        except Exception as e:
            test_log["latency_ms"] = int((time.time() - t0) * 1000)
            msg = str(e)
            external_api_test_success = False
            error_type, recommended_fix = _classify_error(0, msg)
            error_summary = msg[:500]
    else:
        external_api_test_attempted = False
        external_api_test_success = False
        missing = []
        if not api_key_present:
            missing.append("AI_REVIEW_API_KEY")
        if not base_url_present:
            missing.append("AI_REVIEW_BASE_URL")
        if not model_present:
            missing.append("AI_REVIEW_MODEL")
        error_type = "MISSING_ENV"
        error_summary = "missing_env:" + ",".join(missing)
        recommended_fix = "Set required env vars, then retry Stage7K connectivity diagnosis."

    test_log["error_type"] = error_type
    test_log["error_summary"] = error_summary

    _write = lambda p, obj: p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    _write(OUT_LOG, test_log)

    after = _snapshot()
    production_files_modified = not (
        before["01"] == after["01"]
        and before["02"] == after["02"]
        and before["02A"] == after["02A"]
        and before["05"] == after["05"]
        and before["06"] == after["06"]
    )
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    check_status = _delivery_status()

    summary = {
        "stage": "stage7k_fix_ai_connectivity_diagnosis",
        "mode": "connectivity_diagnosis_only",
        "based_on_stage7k_commit": "91041900b6f5d53be5f3e7cae2d2ddf9d1e4a0a4",
        "provider": "openai_compatible",
        "model": _norm(model),
        "api_key_present": api_key_present,
        "api_key_logged": False,
        "base_url_present": base_url_present,
        "model_present": model_present,
        "external_api_test_attempted": external_api_test_attempted,
        "external_api_test_success": external_api_test_success,
        "http_status": http_status,
        "error_type": error_type,
        "error_summary": error_summary,
        "recommended_fix": recommended_fix,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": check_status,
        "ready_for_stage7k_retry_real_ai_api_sandbox": bool(
            api_key_present and base_url_present and model_present and not external_api_test_success
        ),
    }
    _write(OUT_SUMMARY, summary)

    report = "\n".join(
        [
            "# Stage7K-Fix AI Connectivity Diagnosis",
            "",
            f"- api_key_present: {summary['api_key_present']}",
            f"- base_url_present: {summary['base_url_present']}",
            f"- model_present: {summary['model_present']}",
            f"- external_api_test_attempted: {summary['external_api_test_attempted']}",
            f"- external_api_test_success: {summary['external_api_test_success']}",
            f"- http_status: {summary['http_status']}",
            f"- error_type: {summary['error_type']}",
            f"- error_summary: {summary['error_summary']}",
            f"- recommended_fix: {summary['recommended_fix']}",
            "",
            "## Safety",
            "- API key value was never logged.",
            "- Only one lightweight API test was executed at most.",
            f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        ]
    )
    OUT_REPORT.write_text(report, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
