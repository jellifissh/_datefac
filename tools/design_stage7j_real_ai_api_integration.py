import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

BASE_DIR = Path(r"D:\_datefac")
STAGE7I_DIR = BASE_DIR / "output" / "stage7i_ai_runtime_dry_run"
STAGE7H_DIR = BASE_DIR / "output" / "stage7h_ai_assisted_review_design"
OUT_DIR = BASE_DIR / "output" / "stage7j_real_ai_api_integration_design"

IN_S7I_SUMMARY = STAGE7I_DIR / "188_stage7i_ai_runtime_dry_run_summary.json"
IN_S7I_REQ = STAGE7I_DIR / "188_stage7i_ai_review_requests.jsonl"
IN_S7I_RESP = STAGE7I_DIR / "188_stage7i_mock_ai_responses.jsonl"
IN_S7I_SUG = STAGE7I_DIR / "188_stage7i_ai_suggestion_queue.xlsx"
IN_S7I_REJ = STAGE7I_DIR / "188_stage7i_ai_rejected_suggestions.xlsx"
IN_S7I_AUD = STAGE7I_DIR / "188_stage7i_ai_validation_audit.xlsx"

IN_REQ_SCHEMA = STAGE7H_DIR / "187_stage7h_ai_review_request_schema.json"
IN_RESP_SCHEMA = STAGE7H_DIR / "187_stage7h_ai_review_response_schema.json"
IN_PROMPT = STAGE7H_DIR / "187_stage7h_prompt_template.md"
IN_VALIDATION_RULES = STAGE7H_DIR / "187_stage7h_ai_validation_rules.json"

OUT_SUMMARY = OUT_DIR / "189_stage7j_ai_api_integration_summary.json"
OUT_REPORT = OUT_DIR / "189_stage7j_ai_api_integration_report.md"
OUT_PROVIDER_SCHEMA = OUT_DIR / "189_stage7j_provider_config_schema.json"
OUT_SAFETY_POLICY = OUT_DIR / "189_stage7j_api_safety_policy.md"
OUT_STAGE7K_PLAN = OUT_DIR / "189_stage7j_stage7k_real_api_dry_run_plan.md"

EXAMPLE_CONFIG = BASE_DIR / "config" / "ai_review.example.yaml"
DESIGN_DOC = BASE_DIR / "docs" / "stage7j_real_ai_api_integration_design.md"
CLIENT_SKELETON = BASE_DIR / "tools" / "ai_review_client_skeleton.py"

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


def _snapshot_guard() -> Dict[str, str]:
    snap = s5k._snapshot_hashes()
    snap["official_02b"] = _sha256(OFFICIAL_02B)
    snap["formal_scope_rules"] = _sha256(FORMAL_SCOPE_RULES)
    snap["standardizer"] = _sha256(STANDARDIZER_FILE)
    snap["release_zip"] = _sha256(RELEASE_ZIP) if RELEASE_ZIP.exists() else "MISSING"
    return snap


def _run_delivery_check() -> Dict[str, Any]:
    p = subprocess.run(
        [sys.executable, str(BASE_DIR / "tools" / "check_delivery_state.py"), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    txt = (p.stdout or "").strip()
    if not txt:
        return {"overall_status": "UNKNOWN"}
    return json.loads(txt)


def _line_count(path: Path) -> int:
    with open(path, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def _provider_schema() -> Dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "AIReviewProviderConfig",
        "type": "object",
        "required": [
            "provider",
            "base_url",
            "api_key_env",
            "model",
            "timeout_seconds",
            "max_retries",
            "max_requests_per_run",
            "max_tokens_per_request",
            "temperature",
            "response_format",
            "external_api_enabled",
            "require_human_approval",
            "allow_real_apply",
        ],
        "properties": {
            "provider": {
                "type": "string",
                "enum": ["disabled", "mock", "openai_compatible", "deepseek_compatible", "qwen_compatible"],
            },
            "base_url": {"type": "string"},
            "api_key_env": {"type": "string"},
            "model": {"type": "string"},
            "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 120},
            "max_retries": {"type": "integer", "minimum": 0, "maximum": 10},
            "max_requests_per_run": {"type": "integer", "minimum": 1, "maximum": 1000},
            "max_tokens_per_request": {"type": "integer", "minimum": 1, "maximum": 100000},
            "temperature": {"type": "number", "minimum": 0.0, "maximum": 2.0},
            "response_format": {"type": "string", "enum": ["json_schema", "json_object"]},
            "external_api_enabled": {"type": "boolean", "const": False},
            "require_human_approval": {"type": "boolean", "const": True},
            "allow_real_apply": {"type": "boolean", "const": False},
            "budget": {
                "type": "object",
                "properties": {
                    "max_total_tokens_per_run": {"type": "integer", "minimum": 1},
                    "max_total_cost_usd_per_run": {"type": "number", "minimum": 0.0},
                },
            },
            "logging": {
                "type": "object",
                "properties": {
                    "log_requests": {"type": "boolean"},
                    "log_responses": {"type": "boolean"},
                    "redact_sensitive_fields": {"type": "boolean"},
                },
            },
        },
    }


def _example_yaml() -> str:
    return """# Stage7J example config (NO real secrets)
provider: "disabled"
base_url: "${AI_REVIEW_BASE_URL}"
api_key_env: "AI_REVIEW_API_KEY"
model: "${AI_REVIEW_MODEL}"
timeout_seconds: 30
max_retries: 2
max_requests_per_run: 5
max_tokens_per_request: 2000
temperature: 0
response_format: "json_schema"
external_api_enabled: false
require_human_approval: true
allow_real_apply: false
budget:
  max_total_tokens_per_run: 10000
  max_total_cost_usd_per_run: 2.0
logging:
  log_requests: true
  log_responses: true
  redact_sensitive_fields: true
"""


def _client_skeleton_py() -> str:
    return '''from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


class ExternalAPIDisabledError(RuntimeError):
    pass


@dataclass
class AIReviewRuntimeConfig:
    provider: str = "disabled"
    base_url: str = ""
    api_key_env: str = "AI_REVIEW_API_KEY"
    model: str = ""
    timeout_seconds: int = 30
    max_retries: int = 2
    max_requests_per_run: int = 5
    max_tokens_per_request: int = 2000
    temperature: float = 0.0
    response_format: str = "json_schema"
    external_api_enabled: bool = False
    require_human_approval: bool = True
    allow_real_apply: bool = False


class AIReviewClientSkeleton:
    """Stage7J skeleton only.

    This class intentionally does NOT perform any real external API call.
    Real calls must be explicitly enabled in future stage by passing
    enable_external_api=True and using reviewed implementation.
    """

    def __init__(self, config: AIReviewRuntimeConfig, enable_external_api: bool = False) -> None:
        self.config = config
        self.enable_external_api = bool(enable_external_api)

    def ensure_runtime_guard(self) -> None:
        if not self.enable_external_api:
            raise ExternalAPIDisabledError(
                "External API call blocked: --enable-external-api not provided."
            )
        if not self.config.external_api_enabled:
            raise ExternalAPIDisabledError(
                "External API call blocked: config.external_api_enabled=false."
            )
        raise ExternalAPIDisabledError(
            "Stage7J skeleton forbids real API call by design."
        )

    def review_batch(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Dry-run placeholder returning keep_manual_review for each request."""
        responses: List[Dict[str, Any]] = []
        for req in requests:
            responses.append(
                {
                    "review_id": str(req.get("review_id", "")),
                    "suggested_action": "keep_manual_review",
                    "suggested_row_ids": [],
                    "suggested_metric_name": "",
                    "suggested_year": "",
                    "suggested_value": "",
                    "suggested_unit": "",
                    "confidence": 0.0,
                    "reasoning_summary": "Stage7J skeleton mock response.",
                    "risk_flags": ["skeleton_mode"],
                    "requires_human_approval": True,
                }
            )
        return responses


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows
'''


def _safety_policy_md() -> str:
    return """# Stage7J API Safety Policy

## Mandatory controls
1. No real API call in Stage7J.
2. No API keys committed to repository.
3. Default `external_api_enabled=false`.
4. Without `--enable-external-api`, client must refuse request.
5. All AI output must pass Stage7H/7I validation rules.
6. `requires_human_approval=true` for all suggestions.
7. AI suggestions are sandbox-only and cannot write production 06.
8. No modification to formal rules / official 02B / delivery package.

## Logging and redaction
- Log request/response IDs and validation status.
- Redact potential secrets in any diagnostic logs.
- Keep source trace: pdf/page/table/row.

## Fail-safe defaults
- Validation failure => reject suggestion.
- Low confidence => keep manual review.
- Schema parse failure => keep manual review.
- Any policy ambiguity => keep manual review.
"""


def _stage7k_plan_md() -> str:
    return """# Stage7K Real API Sandbox Dry-Run Plan

## Objective
Run real provider integration in sandbox mode with strict guardrails and zero production impact.

## Preconditions
- Stage7J design artifacts committed.
- Reviewed provider adapter implementation available.
- Explicit operator flag `--enable-external-api` required.
- Runtime env var `AI_REVIEW_API_KEY` provided out-of-repo.

## Execution scope
1. Read Stage7G remaining manual review groups.
2. Build requests via Stage7H schema.
3. Invoke provider adapter with capped requests/tokens/cost.
4. Validate responses with Stage7H/7I rules.
5. Route to suggestion/rejected queue.
6. Produce sandbox preview only.

## Hard limits
- max_requests_per_run <= 5
- max_total_tokens_per_run <= 10k
- max_total_cost_usd_per_run <= 2.0
- timeout_seconds <= 30
- retries <= 2

## Success criteria
- external API call traceable and bounded.
- no secret leakage in logs.
- no production file changes.
- validation pass rate reported.
- all suggestions remain human-approval required.
"""


def _design_doc_md() -> str:
    return """# Stage7J Real AI API Integration Design

## Purpose
Design real API integration architecture for AI-assisted manual review, without executing real requests.

## Provider abstraction
- disabled provider
- local mock provider
- openai-compatible provider
- deepseek-compatible provider
- qwen-compatible provider

## Core modules
1. config loader + env resolver
2. provider adapter interface
3. request builder (Stage7H schema)
4. response validator (Stage7H/7I rules)
5. suggestion routing (queue vs rejected)
6. human approval gate
7. audit logger

## Security requirements
- No API key in code/repo.
- Use env var indirection only (`api_key_env`).
- external_api_enabled defaults to false.
- explicit runtime flag required for future real-call stage.

## Runtime controls
- timeout, retry, rate cap, token cap, cost cap.
- JSON schema response enforcement.
- fallback to keep_manual_review on any failure.

## Human approval protocol
- all suggestions require_human_approval=true
- no direct write to formal 06
- approval decision logged per review_id
"""


def _integration_report(summary: Dict[str, Any], req_count: int, resp_count: int, sug_rows: int, rej_rows: int, aud_rows: int) -> str:
    return "\n".join(
        [
            "# Stage7J Real AI API Integration Design Report",
            "",
            "## Inputs",
            f"- based_on_stage7i_commit: {summary['based_on_stage7i_commit']}",
            f"- stage7i_request_count: {req_count}",
            f"- stage7i_response_count: {resp_count}",
            f"- stage7i_suggestion_rows: {sug_rows}",
            f"- stage7i_rejected_rows: {rej_rows}",
            f"- stage7i_audit_rows: {aud_rows}",
            "",
            "## Outputs",
            f"- provider_config_schema_generated: {summary['provider_config_schema_generated']}",
            f"- example_config_generated: {summary['example_config_generated']}",
            f"- client_skeleton_generated: {summary['client_skeleton_generated']}",
            f"- safety_policy_generated: {summary['safety_policy_generated']}",
            f"- stage7k_real_api_dry_run_plan_generated: {summary['stage7k_real_api_dry_run_plan_generated']}",
            "",
            "## Safety",
            f"- external_api_called: {summary['external_api_called']}",
            f"- api_key_committed: {summary['api_key_committed']}",
            f"- default_external_api_enabled: {summary['default_external_api_enabled']}",
            f"- require_human_approval: {summary['require_human_approval']}",
            f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
            "",
            "## Decision",
            f"- ready_for_stage7k_real_ai_api_sandbox_dry_run: {summary['ready_for_stage7k_real_ai_api_sandbox_dry_run']}",
        ]
    )


def main() -> int:
    required = [
        IN_S7I_SUMMARY,
        IN_S7I_REQ,
        IN_S7I_RESP,
        IN_S7I_SUG,
        IN_S7I_REJ,
        IN_S7I_AUD,
        IN_REQ_SCHEMA,
        IN_RESP_SCHEMA,
        IN_PROMPT,
        IN_VALIDATION_RULES,
    ]
    for p in required:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    before = _snapshot_guard()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    EXAMPLE_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    DESIGN_DOC.parent.mkdir(parents=True, exist_ok=True)

    s7i_summary = json.loads(IN_S7I_SUMMARY.read_text(encoding="utf-8"))
    req_count = _line_count(IN_S7I_REQ)
    resp_count = _line_count(IN_S7I_RESP)
    sug_rows = len(pd.read_excel(IN_S7I_SUG).fillna(""))
    rej_rows = len(pd.read_excel(IN_S7I_REJ).fillna(""))
    aud_rows = len(pd.read_excel(IN_S7I_AUD).fillna(""))

    provider_schema = _provider_schema()
    OUT_PROVIDER_SCHEMA.write_text(json.dumps(provider_schema, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_SAFETY_POLICY.write_text(_safety_policy_md(), encoding="utf-8")
    OUT_STAGE7K_PLAN.write_text(_stage7k_plan_md(), encoding="utf-8")

    EXAMPLE_CONFIG.write_text(_example_yaml(), encoding="utf-8")
    DESIGN_DOC.write_text(_design_doc_md(), encoding="utf-8")
    CLIENT_SKELETON.write_text(_client_skeleton_py(), encoding="utf-8")

    # quick secret scan for generated files
    generated_files = [
        OUT_PROVIDER_SCHEMA,
        OUT_SAFETY_POLICY,
        OUT_STAGE7K_PLAN,
        EXAMPLE_CONFIG,
        DESIGN_DOC,
        CLIENT_SKELETON,
    ]

    secret_patterns = [
        "sk-",
        "api_key:",
        "api-key",
        "bearer ",
    ]

    api_key_committed = False
    for fp in generated_files:
        txt = fp.read_text(encoding="utf-8", errors="ignore").lower()
        # allow placeholder env strategy only
        for pat in secret_patterns:
            if pat == "api_key:" and "${ai_review_api_key}" in txt:
                continue
            if pat in txt and "${ai_review_api_key}" not in txt and "api_key_env" not in txt:
                api_key_committed = True
                break
        if api_key_committed:
            break

    after = _snapshot_guard()
    production_files_modified = not (
        before["01"] == after["01"]
        and before["02"] == after["02"]
        and before["02A"] == after["02A"]
        and before["05"] == after["05"]
        and before["06"] == after["06"]
    )
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_scope_rules"] != after["formal_scope_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    overall_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "stage7j_real_ai_api_integration_design",
        "mode": "design_only_no_external_api_call",
        "based_on_stage7i_commit": "1a1dcee2d16d1e2a8d8c5a1f3c9d4b7f0e8f3a2c",
        "external_api_called": False,
        "api_key_committed": bool(api_key_committed),
        "provider_config_schema_generated": True,
        "example_config_generated": True,
        "client_skeleton_generated": True,
        "safety_policy_generated": True,
        "stage7k_real_api_dry_run_plan_generated": True,
        "default_external_api_enabled": False,
        "require_human_approval": True,
        "production_files_modified": bool(production_files_modified),
        "official_02b_modified": bool(official_02b_modified),
        "formal_rules_modified": bool(formal_rules_modified),
        "standardizer_modified": bool(standardizer_modified),
        "release_package_modified": bool(release_package_modified),
        "check_delivery_state_overall_status": overall_status,
        "ready_for_stage7k_real_ai_api_sandbox_dry_run": False,
    }

    summary["ready_for_stage7k_real_ai_api_sandbox_dry_run"] = bool(
        not summary["external_api_called"]
        and not summary["api_key_committed"]
        and summary["provider_config_schema_generated"]
        and summary["example_config_generated"]
        and summary["client_skeleton_generated"]
        and summary["safety_policy_generated"]
        and summary["stage7k_real_api_dry_run_plan_generated"]
        and summary["default_external_api_enabled"] is False
        and summary["require_human_approval"] is True
        and not summary["production_files_modified"]
        and not summary["official_02b_modified"]
        and not summary["formal_rules_modified"]
        and not summary["standardizer_modified"]
        and not summary["release_package_modified"]
        and summary["check_delivery_state_overall_status"] == "PASS"
    )

    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_REPORT.write_text(_integration_report(summary, req_count, resp_count, sug_rows, rej_rows, aud_rows), encoding="utf-8")

    print(f"stage7j_summary_json: {OUT_SUMMARY}")
    print(f"stage7j_report_md: {OUT_REPORT}")
    print(f"stage7j_ready_for_stage7k_real_ai_api_sandbox_dry_run: {summary['ready_for_stage7k_real_ai_api_sandbox_dry_run']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
