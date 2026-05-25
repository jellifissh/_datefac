import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Tuple
from urllib.parse import urlparse, urlunparse

import requests

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

BASE_DIR = Path(r"D:\_datefac")
OUT_DIR = BASE_DIR / "output" / "stage7k_fix2_glm_api_connectivity"
OUT_SUMMARY = OUT_DIR / "192_stage7k_fix2_glm_api_connectivity_summary.json"
OUT_REPORT = OUT_DIR / "192_stage7k_fix2_glm_api_connectivity_report.md"
OUT_LOG = OUT_DIR / "192_stage7k_fix2_connection_test_log.json"
OUT_ENV = OUT_DIR / "192_stage7k_fix2_sanitized_env_check.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

# at most 2 real external calls
MAX_EXTERNAL_TEST_CALLS = 2


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        try:
            import math
            if math.isnan(v):
                return ""
        except Exception:
            pass
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


def _sanitize_url(url: str) -> str:
    try:
        u = urlparse(url)
        netloc = u.hostname or ""
        if u.port:
            netloc = f"{netloc}:{u.port}"
        path = u.path or ""
        return urlunparse((u.scheme, netloc, path, "", "", ""))
    except Exception:
        return ""


def _base_url_likely_web_root(url: str) -> bool:
    s = _sanitize_url(url)
    if not s:
        return False
    u = urlparse(s)
    p = (u.path or "").rstrip("/")
    # likely pure website root if no API-like path
    return p == ""


def _classify_error(http_status: Any, err_text: str) -> str:
    t = (err_text or "").lower()
    hs = int(http_status) if isinstance(http_status, int) else None

    if hs is not None:
        if hs == 401:
            return "HTTP_401_UNAUTHORIZED"
        if hs == 403:
            return "HTTP_403_FORBIDDEN"
        if hs == 404:
            return "HTTP_404_NOT_FOUND"
        if hs == 429:
            return "HTTP_429_RATE_LIMIT"
        if hs >= 500:
            return "HTTP_5XX_SERVER_ERROR"

    if "winerror 10013" in t:
        return "WINERROR_10013_POLICY_DENIED"
    if "name or service not known" in t or "getaddrinfo" in t or "dns" in t:
        return "DNS_ERROR"
    if "timed out" in t or "timeout" in t:
        return "CONNECTION_TIMEOUT"
    if "refused" in t:
        return "CONNECTION_REFUSED"
    if "ssl" in t or "tls" in t or "certificate" in t:
        return "TLS_SSL_ERROR"
    if "proxy" in t:
        return "PROXY_ERROR"
    if "json" in t and "parse" in t:
        return "RESPONSE_NOT_JSON"
    if "choices" in t or "message" in t:
        return "OPENAI_COMPAT_FORMAT_ERROR"
    return "UNKNOWN_ERROR"


def _proxy_info() -> Tuple[bool, str, str, str]:
    p = subprocess.run(
        ["netsh", "winhttp", "show", "proxy"],
        capture_output=True,
        text=True,
        check=False,
    )
    out = (p.stdout or "").strip()
    line = ""
    for l in out.splitlines():
        ll = l.strip()
        if ll:
            line = ll
    proxy_detected = "Direct access (no proxy server)" not in out

    http_proxy = _norm(os.environ.get("HTTP_PROXY", ""))
    https_proxy = _norm(os.environ.get("HTTPS_PROXY", ""))
    return proxy_detected, out, http_proxy, https_proxy


def _git_unpushed_stage7k_fix() -> bool:
    p = subprocess.run(
        ["git", "-C", str(BASE_DIR), "log", "--oneline", "origin/main..HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    txt = (p.stdout or "")
    return "a1ee531" in txt


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    before = _snapshot()

    api_key = _norm(os.environ.get("AI_REVIEW_API_KEY", ""))
    base_url = _norm(os.environ.get("AI_REVIEW_BASE_URL", ""))
    model = _norm(os.environ.get("AI_REVIEW_MODEL", ""))

    api_key_present = bool(api_key)
    base_url_present = bool(base_url)
    model_present = bool(model)
    base_url_sanitized = _sanitize_url(base_url)
    base_url_likely_web_root = _base_url_likely_web_root(base_url)

    env_payload = {
        "api_key_present": api_key_present,
        "api_key_logged": False,
        "base_url_present": base_url_present,
        "model_present": model_present,
        "model_value": model,
        "base_url_sanitized": base_url_sanitized,
        "base_url_likely_web_root": base_url_likely_web_root,
    }
    OUT_ENV.write_text(json.dumps(env_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    proxy_detected, winhttp_proxy, http_proxy, https_proxy = _proxy_info()

    # no review processing
    real_review_group_processed = False

    test_log: Dict[str, Any] = {
        "test_call_limit": MAX_EXTERNAL_TEST_CALLS,
        "calls": [],
        "api_key_logged": False,
        "base_url_sanitized": base_url_sanitized,
    }

    external_api_test_attempted = False
    external_api_test_success = False
    http_status = None
    response_looks_like_html = False
    response_json_parse_success = False
    error_type = ""
    error_summary = ""
    recommended_fix = ""

    calls_used = 0

    # Call #1: web root reachability
    web_root_reachable = False
    if base_url_present:
        external_api_test_attempted = True
        calls_used += 1
        t0 = time.time()
        try:
            r = requests.get(base_url_sanitized or base_url, timeout=15)
            latency_ms = int((time.time() - t0) * 1000)
            ctype = _norm(r.headers.get("Content-Type", ""))
            body_prefix = (r.text or "")[:200]
            response_looks_like_html = "<html" in body_prefix.lower() or "text/html" in ctype.lower()
            web_root_reachable = 200 <= r.status_code < 500
            test_log["calls"].append(
                {
                    "name": "web_root_test",
                    "url": base_url_sanitized,
                    "http_status": r.status_code,
                    "latency_ms": latency_ms,
                    "content_type": ctype,
                    "response_looks_like_html": response_looks_like_html,
                    "error": "",
                }
            )
        except Exception as e:
            latency_ms = int((time.time() - t0) * 1000)
            et = _classify_error(None, str(e))
            test_log["calls"].append(
                {
                    "name": "web_root_test",
                    "url": base_url_sanitized,
                    "http_status": None,
                    "latency_ms": latency_ms,
                    "content_type": "",
                    "response_looks_like_html": False,
                    "error": str(e)[:500],
                    "error_type": et,
                }
            )

    # Call #2: minimal chat/completions check
    if api_key_present and base_url_present and model_present and calls_used < MAX_EXTERNAL_TEST_CALLS:
        calls_used += 1
        chat_url = (base_url.rstrip("/") + "/chat/completions")
        chat_url_sanitized = _sanitize_url(chat_url)
        t0 = time.time()
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "Return strict JSON only."},
                    {"role": "user", "content": '请只返回 JSON：{"ok":true}'},
                ],
                "temperature": 0,
                "max_tokens": 50,
                "response_format": {"type": "json_object"},
            }
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            r = requests.post(chat_url, headers=headers, json=payload, timeout=30)
            latency_ms = int((time.time() - t0) * 1000)
            http_status = int(r.status_code)

            body_text = r.text or ""
            response_looks_like_html = response_looks_like_html or ("<html" in body_text[:200].lower())

            if 200 <= r.status_code < 300:
                try:
                    obj = r.json()
                    response_json_parse_success = True
                    # OpenAI-compatible minimal structure check
                    choices = obj.get("choices", []) if isinstance(obj, dict) else []
                    if choices and isinstance(choices, list):
                        msg = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
                        _ = _norm(msg.get("content", ""))
                        external_api_test_success = True
                    else:
                        external_api_test_success = False
                        error_type = "OPENAI_COMPAT_FORMAT_ERROR"
                        error_summary = "HTTP 200 but missing OpenAI-compatible choices/message fields"
                except Exception as e:
                    external_api_test_success = False
                    response_json_parse_success = False
                    error_type = "RESPONSE_NOT_JSON"
                    error_summary = str(e)[:500]
            else:
                external_api_test_success = False
                error_type = _classify_error(http_status, body_text)
                error_summary = f"HTTP {http_status}: {(body_text or '')[:300]}"

            test_log["calls"].append(
                {
                    "name": "chat_completions_test",
                    "url": chat_url_sanitized,
                    "http_status": http_status,
                    "latency_ms": latency_ms,
                    "response_looks_like_html": response_looks_like_html,
                    "response_json_parse_success": response_json_parse_success,
                    "error_type": error_type,
                    "error": error_summary,
                }
            )
        except Exception as e:
            latency_ms = int((time.time() - t0) * 1000)
            external_api_test_success = False
            error_type = _classify_error(None, str(e))
            error_summary = str(e)[:500]
            test_log["calls"].append(
                {
                    "name": "chat_completions_test",
                    "url": _sanitize_url(base_url.rstrip("/") + "/chat/completions"),
                    "http_status": None,
                    "latency_ms": latency_ms,
                    "response_looks_like_html": False,
                    "response_json_parse_success": False,
                    "error_type": error_type,
                    "error": error_summary,
                }
            )
    else:
        # config missing or call limit reached
        if not error_type and (not api_key_present or not base_url_present or not model_present):
            error_type = "UNKNOWN_ERROR"
            error_summary = "missing required env for API test"

    if not external_api_test_success and not recommended_fix:
        if base_url_likely_web_root:
            recommended_fix = "AI_REVIEW_BASE_URL 疑似网页根地址，请改为平台文档要求的 OpenAI-compatible API base URL（以官方文档为准）。"
        elif error_type == "WINERROR_10013_POLICY_DENIED":
            recommended_fix = "检查 Windows 防火墙/杀软/终端安全策略/代理，放通 open.bigmodel.cn:443 对 Python/Codex 进程的访问。"
        elif error_type in {"CONNECTION_REFUSED", "CONNECTION_TIMEOUT", "DNS_ERROR", "CONNECTION_ERROR", "TLS_SSL_ERROR", "PROXY_ERROR"}:
            recommended_fix = "先修复网络出口或代理策略，再重试 Stage 7K。"
        elif error_type.startswith("HTTP_"):
            recommended_fix = "根据 HTTP 状态码修正 base_url、鉴权、配额或模型权限。"
        else:
            recommended_fix = "根据 connection_test_log 的具体错误修正 endpoint/网络后重试。"

    OUT_LOG.write_text(json.dumps(test_log, ensure_ascii=False, indent=2), encoding="utf-8")

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

    summary = {
        "stage": "stage7k_fix2_glm_api_connectivity",
        "mode": "connectivity_diagnosis_only",
        "based_on_stage7k_commit": "91041900b6f5d53be5f3e7cae2d2ddf9d1e4a0a4",
        "local_unpushed_stage7k_fix_commit_detected": _git_unpushed_stage7k_fix(),
        "provider": "openai_compatible",
        "model": model,
        "api_key_present": api_key_present,
        "api_key_logged": False,
        "base_url_present": base_url_present,
        "model_present": model_present,
        "base_url_sanitized": base_url_sanitized,
        "base_url_likely_web_root": base_url_likely_web_root,
        "web_root_reachable": web_root_reachable,
        "chat_completions_url_constructed": base_url_present,
        "external_api_test_attempted": external_api_test_attempted,
        "external_api_test_success": external_api_test_success,
        "http_status": http_status,
        "response_looks_like_html": response_looks_like_html,
        "response_json_parse_success": response_json_parse_success,
        "error_type": error_type,
        "error_summary": error_summary,
        "proxy_detected": proxy_detected,
        "winhttp_proxy": winhttp_proxy,
        "recommended_fix": recommended_fix,
        "real_review_group_processed": False,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": _delivery_status(),
        "ready_for_stage7k_retry_real_ai_api_sandbox": bool(
            api_key_present
            and base_url_present
            and model_present
            and (external_api_test_success or error_type in {"HTTP_401_UNAUTHORIZED", "HTTP_403_FORBIDDEN", "HTTP_404_NOT_FOUND", "HTTP_429_RATE_LIMIT", "HTTP_5XX_SERVER_ERROR", "OPENAI_COMPAT_FORMAT_ERROR", "RESPONSE_NOT_JSON", "WINERROR_10013_POLICY_DENIED", "CONNECTION_TIMEOUT", "CONNECTION_REFUSED", "DNS_ERROR", "PROXY_ERROR", "TLS_SSL_ERROR", "UNKNOWN_ERROR"})
        ),
    }

    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    report = "\n".join(
        [
            "# Stage7K-Fix2 GLM API Connectivity Diagnosis",
            "",
            f"- local_unpushed_stage7k_fix_commit_detected: {summary['local_unpushed_stage7k_fix_commit_detected']}",
            f"- api_key_present: {summary['api_key_present']}",
            f"- base_url_present: {summary['base_url_present']}",
            f"- model_present: {summary['model_present']}",
            f"- model: {summary['model']}",
            f"- base_url_sanitized: {summary['base_url_sanitized']}",
            f"- base_url_likely_web_root: {summary['base_url_likely_web_root']}",
            f"- web_root_reachable: {summary['web_root_reachable']}",
            f"- external_api_test_attempted: {summary['external_api_test_attempted']}",
            f"- external_api_test_success: {summary['external_api_test_success']}",
            f"- http_status: {summary['http_status']}",
            f"- response_looks_like_html: {summary['response_looks_like_html']}",
            f"- response_json_parse_success: {summary['response_json_parse_success']}",
            f"- error_type: {summary['error_type']}",
            f"- error_summary: {summary['error_summary']}",
            f"- proxy_detected: {summary['proxy_detected']}",
            "",
            "## WinHTTP Proxy",
            summary["winhttp_proxy"],
            "",
            "## Recommended Fix",
            summary["recommended_fix"],
            "",
            "## Safety",
            "- API key value is never logged.",
            f"- max external test calls allowed: {MAX_EXTERNAL_TEST_CALLS}",
            f"- real_review_group_processed: {summary['real_review_group_processed']}",
            f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        ]
    )
    OUT_REPORT.write_text(report, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
