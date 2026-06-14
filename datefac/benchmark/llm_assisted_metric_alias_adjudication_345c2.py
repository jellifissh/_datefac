from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from datefac.llm.client import ChatCompletionsClient
from datefac.llm.config import resolve_ai_review_runtime_config
from datefac.llm.json_utils import parse_model_json
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION = "LLM_ASSISTED_METRIC_ALIAS_ADJUDICATION_345C2_READY"
REQUEST_ONLY_DECISION = "LLM_ALIAS_ADJUDICATION_REQUEST_PACKAGE_345C2_READY"
FIXTURE_DECISION = "LLM_ALIAS_ADJUDICATION_FIXTURE_345C2_READY"
INPUT_STAGE = "POST_345C_LLM_ALIAS_ADJUDICATION"
PROMPT_VERSION = "345C2_v1"

DEFAULT_345C_DIR = Path(r"D:\_datefac\output\metric_candidate_normalization_coverage_345c")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\llm_assisted_metric_alias_adjudication_345c2")
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_MAX_ALIAS_CANDIDATES = 26

MANIFEST_FILE_NAME = "llm_assisted_metric_alias_adjudication_345c2_manifest.json"
REQUEST_PACKAGE_JSON_FILE_NAME = (
    "llm_assisted_metric_alias_adjudication_345c2_alias_request_package.json"
)
REQUEST_PACKAGE_CSV_FILE_NAME = (
    "llm_assisted_metric_alias_adjudication_345c2_alias_request_package.csv"
)
SUGGESTIONS_JSON_FILE_NAME = (
    "llm_assisted_metric_alias_adjudication_345c2_alias_suggestions.json"
)
SUGGESTIONS_CSV_FILE_NAME = (
    "llm_assisted_metric_alias_adjudication_345c2_alias_suggestions.csv"
)
REVIEW_REQUIRED_JSON_FILE_NAME = (
    "llm_assisted_metric_alias_adjudication_345c2_review_required.json"
)
REVIEW_REQUIRED_CSV_FILE_NAME = (
    "llm_assisted_metric_alias_adjudication_345c2_review_required.csv"
)
RESPONSE_AUDIT_JSON_FILE_NAME = (
    "llm_assisted_metric_alias_adjudication_345c2_response_audit.json"
)
PROMPT_AUDIT_MD_FILE_NAME = (
    "llm_assisted_metric_alias_adjudication_345c2_prompt_audit.md"
)
EXECUTIVE_SUMMARY_MD_FILE_NAME = (
    "llm_assisted_metric_alias_adjudication_345c2_executive_summary.md"
)
ARTIFACT_INDEX_MD_FILE_NAME = (
    "llm_assisted_metric_alias_adjudication_345c2_artifact_index.md"
)
NEXT_PLAN_MD_FILE_NAME = "llm_assisted_metric_alias_adjudication_345c2_next_plan.md"

INPUT_MANIFEST_NAME = "metric_candidate_normalization_coverage_345c_manifest.json"
INPUT_ALIAS_QUEUE_JSON_NAME = "metric_candidate_normalization_coverage_345c_alias_candidate_queue.json"
INPUT_ALIAS_QUEUE_CSV_NAME = "metric_candidate_normalization_coverage_345c_alias_candidate_queue.csv"
INPUT_RAW_METRIC_SUMMARY_JSON_NAME = "metric_candidate_normalization_coverage_345c_raw_metric_summary.json"
INPUT_RAW_METRIC_SUMMARY_CSV_NAME = "metric_candidate_normalization_coverage_345c_raw_metric_summary.csv"
INPUT_METRIC_ROWS_JSON_NAME = "metric_candidate_normalization_coverage_345c_metric_rows.json"
INPUT_METRIC_ROWS_CSV_NAME = "metric_candidate_normalization_coverage_345c_metric_rows.csv"

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "temp",
]

FORBIDDEN_STAGE_PATHS = [
    "output",
    "temp",
    "input",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "tools/mineru_new_runner.cmd",
]

KNOWN_STANDARD_METRICS = [
    "revenue",
    "net_profit",
    "EPS",
    "PE",
    "PB",
    "ROE",
    "gross_margin",
    "net_margin",
    "revenue_yoy",
    "net_profit_yoy",
    "operating_cash_flow",
    "investing_cash_flow",
    "financing_cash_flow",
    "cash_net_change",
    "total_assets",
    "total_liabilities",
    "shareholder_equity",
    "total_liabilities_and_equity",
]

ALLOWED_ACTIONS = {
    "MAP_TO_EXISTING_STANDARD_METRIC",
    "PROPOSE_NEW_STANDARD_METRIC",
    "EXCLUDE_NON_CORE_METRIC",
    "NEEDS_HUMAN_REVIEW",
    "INSUFFICIENT_EVIDENCE",
}
ALLOWED_CONFIDENCE = {"HIGH", "MEDIUM", "LOW", "UNKNOWN"}

REQUEST_ROW_FIELDS = [
    "alias_adjudication_id",
    "raw_metric_name",
    "frequency",
    "alias_candidate_priority",
    "source_stages",
    "pdf_names",
    "sample_row_ids",
    "quality_severity_distribution",
    "sample_context_lines",
    "standard_metric_universe",
    "llm_mode",
    "prompt_version",
    "prompt_hash",
    "prompt_text",
]

SUGGESTION_FIELDS = [
    "alias_adjudication_id",
    "raw_metric_name",
    "frequency",
    "alias_candidate_priority",
    "source_stages",
    "pdf_names",
    "sample_row_ids",
    "suggested_action",
    "suggested_standard_metric",
    "suggested_new_standard_metric",
    "confidence",
    "reason",
    "evidence_excerpt",
    "risk_flags",
    "needs_human_review",
    "response_parse_status",
    "response_validation_status",
    "llm_mode",
    "llm_provider_env_source",
    "llm_model",
    "prompt_version",
    "prompt_hash",
    "raw_response_hash",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_git_repo(repo_root: Path) -> bool:
    return (repo_root / ".git").exists()


def _run_git(repo_root: Path, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _git_status_porcelain_for_paths(paths: Sequence[str], repo_root: Path) -> List[str]:
    if not _is_git_repo(repo_root):
        return []
    result = _run_git(repo_root, ["status", "--porcelain", "--", *paths])
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.rstrip() for line in result.stdout.splitlines() if line.strip()]


def _git_staged_names_for_paths(paths: Sequence[str], repo_root: Path) -> List[str]:
    lines = _git_status_porcelain_for_paths(paths, repo_root)
    staged: List[str] = []
    for line in lines:
        if line.startswith("__ERROR__::"):
            return [line]
        if len(line) >= 3 and line[0] in {"A", "M", "D", "R", "C", "U", "T"}:
            staged.append(line[3:].strip())
    return staged


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return " ".join(text.split())


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_input_path(base_dir: Path, json_name: str, csv_name: str | None = None) -> Path:
    json_path = base_dir / json_name
    if json_path.exists():
        return json_path
    if csv_name:
        csv_path = base_dir / csv_name
        if csv_path.exists():
            return csv_path
    raise FileNotFoundError(f"Missing required input artifact: {json_path}")


def _load_json_rows(path: Path) -> List[Dict[str, Any]]:
    if path.suffix.lower() != ".json":
        raise ValueError(f"Only JSON input is supported for this task, got: {path}")
    payload = _read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"Expected list JSON payload in {path}")
    return [dict(row) for row in payload]


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sample_ids_to_list(value: Any) -> List[str]:
    return [part for part in _safe_text(value).split("|") if part]


def _stage_values(value: Any) -> List[str]:
    return [part for part in _safe_text(value).split("|") if part]


def _quality_tokens(value: Any) -> List[str]:
    return [part.strip() for part in _safe_text(value).split(",") if part.strip()]


def _build_metric_row_lookup(metric_rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {
        _safe_text(row.get("metric_coverage_row_id")): row
        for row in metric_rows
        if _safe_text(row.get("metric_coverage_row_id"))
    }


def _sample_context_lines(candidate: Mapping[str, Any], metric_lookup: Mapping[str, Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    for row_id in _sample_ids_to_list(candidate.get("sample_row_ids"))[:5]:
        row = metric_lookup.get(row_id, {})
        if not row:
            continue
        lines.append(
            " | ".join(
                filter(
                    None,
                    [
                        row_id,
                        _safe_text(row.get("pdf_name")),
                        _safe_text(row.get("source_stage")),
                        _safe_text(row.get("source_artifact")),
                        _safe_text(row.get("quality_severity")),
                        _safe_text(row.get("quality_issues")),
                        _safe_text(row.get("review_status")),
                        _safe_text(row.get("trust_status")),
                    ],
                )
            )
        )
    return lines


def _determine_selection(
    alias_candidates: List[Dict[str, Any]],
    *,
    max_alias_candidates: int,
    include_medium_priority: bool,
) -> List[Dict[str, Any]]:
    selected: List[Dict[str, Any]] = []
    for row in alias_candidates:
        priority = _safe_text(row.get("suggested_priority")).upper()
        if priority == "HIGH":
            selected.append(dict(row))
        elif include_medium_priority and priority == "MEDIUM":
            selected.append(dict(row))
        if len(selected) >= max_alias_candidates:
            break
    return selected


def _build_prompt_payload(candidate: Mapping[str, Any], sample_context_lines: List[str]) -> Dict[str, Any]:
    return {
        "task": "Alias adjudication for raw financial metric name",
        "boundaries": [
            "Use only the supplied alias candidate context.",
            "Do not invent financial values.",
            "Do not claim formal export or client readiness.",
            "Do not modify normalization rules or official assets.",
            "Return JSON object only.",
        ],
        "allowed_actions": sorted(ALLOWED_ACTIONS),
        "allowed_confidence": sorted(ALLOWED_CONFIDENCE),
        "existing_standard_metric_universe": KNOWN_STANDARD_METRICS,
        "candidate": {
            "raw_metric_name": _safe_text(candidate.get("raw_metric_name")),
            "frequency": int(candidate.get("frequency") or 0),
            "alias_candidate_priority": _safe_text(candidate.get("suggested_priority")),
            "source_stages": _stage_values(candidate.get("source_stages")),
            "pdf_names": _sample_ids_to_list(candidate.get("pdf_names")),
            "sample_row_ids": _sample_ids_to_list(candidate.get("sample_row_ids")),
            "quality_severity_distribution": _quality_tokens(candidate.get("quality_severity_distribution")),
            "sample_context_lines": sample_context_lines,
        },
        "required_response_schema": {
            "suggested_action": "MAP_TO_EXISTING_STANDARD_METRIC | PROPOSE_NEW_STANDARD_METRIC | EXCLUDE_NON_CORE_METRIC | NEEDS_HUMAN_REVIEW | INSUFFICIENT_EVIDENCE",
            "suggested_standard_metric": "string_or_empty",
            "suggested_new_standard_metric": "string_or_empty",
            "confidence": "HIGH | MEDIUM | LOW | UNKNOWN",
            "reason": "short explanation",
            "evidence_excerpt": "short evidence quote from supplied context",
            "risk_flags": ["string"],
        },
    }


def _prompt_text(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)


def _fixture_response_for_candidate(candidate: Mapping[str, Any]) -> str:
    raw_name = _safe_text(candidate.get("raw_metric_name"))
    if raw_name == "BROKEN_JSON_METRIC":
        return "not-json-response"
    if "鍒╂鼎鎬婚" in raw_name:
        payload = {
            "suggested_action": "NEEDS_HUMAN_REVIEW",
            "suggested_standard_metric": "",
            "suggested_new_standard_metric": "",
            "confidence": "MEDIUM",
            "reason": "Could refer to profit-before-tax style concept and needs review.",
            "evidence_excerpt": raw_name,
            "risk_flags": ["AMBIGUOUS_PROFIT_TERM"],
        }
    elif "璧勬湰寮€鏀" in raw_name or "CAPEX" in raw_name.upper():
        payload = {
            "suggested_action": "PROPOSE_NEW_STANDARD_METRIC",
            "suggested_standard_metric": "",
            "suggested_new_standard_metric": "capital_expenditure",
            "confidence": "MEDIUM",
            "reason": "Looks like a recurring metric outside the current standard universe.",
            "evidence_excerpt": raw_name,
            "risk_flags": ["NEW_STANDARD_CANDIDATE"],
        }
    elif "鍚屾瘮" in raw_name or "YOY" in raw_name.upper():
        payload = {
            "suggested_action": "MAP_TO_EXISTING_STANDARD_METRIC",
            "suggested_standard_metric": "revenue_yoy",
            "suggested_new_standard_metric": "",
            "confidence": "HIGH",
            "reason": "The alias clearly indicates year-over-year percentage style metric.",
            "evidence_excerpt": raw_name,
            "risk_flags": [],
        }
    elif "EV/EBITDA" in raw_name.upper():
        payload = {
            "suggested_action": "EXCLUDE_NON_CORE_METRIC",
            "suggested_standard_metric": "",
            "suggested_new_standard_metric": "",
            "confidence": "HIGH",
            "reason": "Valuation multiple is outside the current core standardization scope here.",
            "evidence_excerpt": raw_name,
            "risk_flags": ["OUT_OF_CORE_SCOPE"],
        }
    else:
        payload = {
            "suggested_action": "INSUFFICIENT_EVIDENCE",
            "suggested_standard_metric": "",
            "suggested_new_standard_metric": "",
            "confidence": "LOW",
            "reason": "Sample context is not strong enough for deterministic mapping.",
            "evidence_excerpt": raw_name,
            "risk_flags": ["INSUFFICIENT_ALIAS_CONTEXT"],
        }
    return json.dumps(payload, ensure_ascii=False)


def _validate_response(parsed: Mapping[str, Any] | None) -> Tuple[str, List[str]]:
    errors: List[str] = []
    if not isinstance(parsed, Mapping):
        return "INVALID_RESPONSE", ["response_not_object"]
    action = _safe_text(parsed.get("suggested_action"))
    confidence = _safe_text(parsed.get("confidence")).upper()
    reason = _safe_text(parsed.get("reason"))
    standard_metric = _safe_text(parsed.get("suggested_standard_metric"))
    new_metric = _safe_text(parsed.get("suggested_new_standard_metric"))
    risk_flags = parsed.get("risk_flags")

    if action not in ALLOWED_ACTIONS:
        errors.append("invalid_suggested_action")
    if confidence not in ALLOWED_CONFIDENCE:
        errors.append("invalid_confidence")
    if not reason:
        errors.append("missing_reason")
    if not isinstance(risk_flags, list):
        errors.append("risk_flags_not_list")
    if action == "MAP_TO_EXISTING_STANDARD_METRIC" and standard_metric not in KNOWN_STANDARD_METRICS:
        errors.append("suggested_standard_metric_outside_known_universe")
    if action != "MAP_TO_EXISTING_STANDARD_METRIC" and standard_metric:
        errors.append("unexpected_suggested_standard_metric")
    if action == "PROPOSE_NEW_STANDARD_METRIC" and not new_metric:
        errors.append("missing_suggested_new_standard_metric")
    if action != "PROPOSE_NEW_STANDARD_METRIC" and new_metric:
        errors.append("unexpected_suggested_new_standard_metric")

    text_blob = json.dumps(parsed, ensure_ascii=False)
    blocked_tokens = [
        "client_ready",
        "production_ready",
        "formal_client_export",
        "investment advice",
    ]
    if any(token in text_blob for token in blocked_tokens):
        errors.append("forbidden_export_or_investment_claim")
    return ("VALID" if not errors else "INVALID_RESPONSE"), errors


def _needs_human_review(
    *,
    action: str,
    confidence: str,
    parse_status: str,
    validation_status: str,
) -> bool:
    if parse_status != "PARSED":
        return True
    if validation_status != "VALID":
        return True
    if confidence != "HIGH":
        return True
    if action in {"PROPOSE_NEW_STANDARD_METRIC", "INSUFFICIENT_EVIDENCE"}:
        return True
    return False


def _response_hash(raw_content: str) -> str:
    return _sha256_text(raw_content or "")


def _artifact_rows(output_dir: Path) -> List[Dict[str, str]]:
    return [
        {
            "artifact_name": MANIFEST_FILE_NAME,
            "path": str(output_dir / MANIFEST_FILE_NAME),
            "purpose": "Manifest and gate summary.",
        },
        {
            "artifact_name": REQUEST_PACKAGE_JSON_FILE_NAME,
            "path": str(output_dir / REQUEST_PACKAGE_JSON_FILE_NAME),
            "purpose": "Deterministic alias adjudication request package.",
        },
        {
            "artifact_name": SUGGESTIONS_JSON_FILE_NAME,
            "path": str(output_dir / SUGGESTIONS_JSON_FILE_NAME),
            "purpose": "Parsed sidecar suggestions.",
        },
        {
            "artifact_name": REVIEW_REQUIRED_JSON_FILE_NAME,
            "path": str(output_dir / REVIEW_REQUIRED_JSON_FILE_NAME),
            "purpose": "Rows requiring human follow-up.",
        },
        {
            "artifact_name": RESPONSE_AUDIT_JSON_FILE_NAME,
            "path": str(output_dir / RESPONSE_AUDIT_JSON_FILE_NAME),
            "purpose": "LLM response parse and validation audit.",
        },
        {
            "artifact_name": PROMPT_AUDIT_MD_FILE_NAME,
            "path": str(output_dir / PROMPT_AUDIT_MD_FILE_NAME),
            "purpose": "Prompt boundary and sample prompt audit.",
        },
        {
            "artifact_name": EXECUTIVE_SUMMARY_MD_FILE_NAME,
            "path": str(output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME),
            "purpose": "Human-readable sidecar summary.",
        },
        {
            "artifact_name": NEXT_PLAN_MD_FILE_NAME,
            "path": str(output_dir / NEXT_PLAN_MD_FILE_NAME),
            "purpose": "Next-step recommendation only.",
        },
    ]


def _decision_for_mode(
    *,
    llm_mode: str,
    live_llm_suggestions_generated: bool,
    runtime_config_available: bool,
) -> str:
    if llm_mode == "fixture":
        return FIXTURE_DECISION
    if llm_mode == "request_only":
        return REQUEST_ONLY_DECISION
    if llm_mode == "auto" and not runtime_config_available:
        return REQUEST_ONLY_DECISION
    if llm_mode in {"auto", "live"} and live_llm_suggestions_generated:
        return READY_DECISION
    return REQUEST_ONLY_DECISION


def build_llm_assisted_metric_alias_adjudication_345c2(
    *,
    metric_candidate_normalization_coverage_345c_dir: Path,
    output_dir: Path,
    max_alias_candidates: int = DEFAULT_MAX_ALIAS_CANDIDATES,
    include_medium_priority: bool = False,
    llm_mode: str = "auto",
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    repo_root: Path,
    fixture_responses: Mapping[str, str] | None = None,
    env: Mapping[str, str] | None = None,
) -> Dict[str, Any]:
    llm_mode = _safe_text(llm_mode).lower() or "auto"
    if llm_mode not in {"auto", "live", "request_only", "fixture"}:
        raise ValueError(f"Unsupported llm_mode: {llm_mode}")
    if max_alias_candidates <= 0:
        raise ValueError("max_alias_candidates must be positive.")

    manifest_path = metric_candidate_normalization_coverage_345c_dir / INPUT_MANIFEST_NAME
    alias_queue_path = _require_input_path(
        metric_candidate_normalization_coverage_345c_dir,
        INPUT_ALIAS_QUEUE_JSON_NAME,
        INPUT_ALIAS_QUEUE_CSV_NAME,
    )
    raw_metric_summary_path = _require_input_path(
        metric_candidate_normalization_coverage_345c_dir,
        INPUT_RAW_METRIC_SUMMARY_JSON_NAME,
        INPUT_RAW_METRIC_SUMMARY_CSV_NAME,
    )
    metric_rows_path = _require_input_path(
        metric_candidate_normalization_coverage_345c_dir,
        INPUT_METRIC_ROWS_JSON_NAME,
        INPUT_METRIC_ROWS_CSV_NAME,
    )
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing required input artifact: {manifest_path}")

    official_assets_before = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    input_hashes_before = {
        str(path): sha256_file(path)
        for path in [manifest_path, alias_queue_path, raw_metric_summary_path, metric_rows_path]
    }
    protected_status_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged_before = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    manifest_345c = _read_json(manifest_path)
    if _safe_text(manifest_345c.get("decision")) != "METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_READY":
        raise ValueError("345C manifest is not READY.")

    alias_candidates = _load_json_rows(alias_queue_path)
    _ = _load_json_rows(raw_metric_summary_path)

    selected_candidates = _determine_selection(
        alias_candidates,
        max_alias_candidates=max_alias_candidates,
        include_medium_priority=include_medium_priority,
    )

    needed_sample_ids = {
        sample_id
        for candidate in selected_candidates
        for sample_id in _sample_ids_to_list(candidate.get("sample_row_ids"))
    }
    metric_rows = _load_json_rows(metric_rows_path)
    metric_lookup = {
        row_id: row
        for row_id, row in _build_metric_row_lookup(metric_rows).items()
        if row_id in needed_sample_ids
    }

    runtime_config, env_statuses = resolve_ai_review_runtime_config(
        env=env,
        timeout_seconds=timeout_seconds
    )
    runtime_config_available = runtime_config is not None
    if llm_mode == "live" and not runtime_config_available:
        raise RuntimeError("llm_mode=live requires runtime config, but no config was found.")

    effective_live = llm_mode == "live" or (llm_mode == "auto" and runtime_config_available)
    live_llm_suggestions_generated = False

    request_rows: List[Dict[str, Any]] = []
    suggestion_rows: List[Dict[str, Any]] = []
    review_required_rows: List[Dict[str, Any]] = []
    response_audit_rows: List[Dict[str, Any]] = []

    client: ChatCompletionsClient | None = None
    if effective_live and runtime_config is not None:
        client = ChatCompletionsClient(
            config=runtime_config,
            system_prompt=(
                "You are a strict financial metric alias adjudicator. "
                "Use only provided alias candidate context. "
                "Do not invent values. "
                "Do not claim export readiness. "
                "Return JSON only."
            ),
            temperature=0,
            response_format={"type": "json_object"},
        )

    for index, candidate in enumerate(selected_candidates, start=1):
        alias_adjudication_id = f"345c2::alias::{index:03d}"
        sample_context_lines = _sample_context_lines(candidate, metric_lookup)
        prompt_payload = _build_prompt_payload(candidate, sample_context_lines)
        prompt_text = _prompt_text(prompt_payload)
        prompt_hash = _sha256_text(prompt_text)
        request_row = {
            "alias_adjudication_id": alias_adjudication_id,
            "raw_metric_name": _safe_text(candidate.get("raw_metric_name")),
            "frequency": int(candidate.get("frequency") or 0),
            "alias_candidate_priority": _safe_text(candidate.get("suggested_priority")),
            "source_stages": _safe_text(candidate.get("source_stages")),
            "pdf_names": _safe_text(candidate.get("pdf_names")),
            "sample_row_ids": _safe_text(candidate.get("sample_row_ids")),
            "quality_severity_distribution": _safe_text(candidate.get("quality_severity_distribution")),
            "sample_context_lines": sample_context_lines,
            "standard_metric_universe": "|".join(KNOWN_STANDARD_METRICS),
            "llm_mode": llm_mode,
            "prompt_version": PROMPT_VERSION,
            "prompt_hash": prompt_hash,
            "prompt_text": prompt_text,
        }
        request_rows.append(request_row)

        if llm_mode == "request_only" or (llm_mode == "auto" and not runtime_config_available):
            continue

        raw_content = ""
        parse_method = "not_run"
        parsed_response: Dict[str, Any] | None = None
        parse_status = "NOT_RUN"
        validation_status = "NOT_RUN"
        validation_errors: List[str] = []
        if llm_mode == "fixture":
            raw_content = (
                fixture_responses.get(request_row["raw_metric_name"])
                if fixture_responses
                else _fixture_response_for_candidate(candidate)
            ) or ""
            parsed_response, parse_method = parse_model_json(raw_content)
            parse_status = "PARSED" if parsed_response is not None else "PARSE_FAILED"
        elif client is not None:
            response = client.adjudicate(prompt_text)
            raw_content = _safe_text(response.get("content"))
            parsed_response, parse_method = parse_model_json(raw_content)
            parse_status = "PARSED" if parsed_response is not None else "PARSE_FAILED"
            live_llm_suggestions_generated = True

        if parse_status == "PARSED":
            validation_status, validation_errors = _validate_response(parsed_response)
        else:
            validation_status = "INVALID_RESPONSE"
            validation_errors = ["response_parse_failed"]

        action = _safe_text((parsed_response or {}).get("suggested_action"))
        confidence = _safe_text((parsed_response or {}).get("confidence")).upper()
        suggestion_row = {
            "alias_adjudication_id": alias_adjudication_id,
            "raw_metric_name": request_row["raw_metric_name"],
            "frequency": request_row["frequency"],
            "alias_candidate_priority": request_row["alias_candidate_priority"],
            "source_stages": request_row["source_stages"],
            "pdf_names": request_row["pdf_names"],
            "sample_row_ids": request_row["sample_row_ids"],
            "suggested_action": action,
            "suggested_standard_metric": _safe_text((parsed_response or {}).get("suggested_standard_metric")),
            "suggested_new_standard_metric": _safe_text((parsed_response or {}).get("suggested_new_standard_metric")),
            "confidence": confidence or "UNKNOWN",
            "reason": _safe_text((parsed_response or {}).get("reason")),
            "evidence_excerpt": _safe_text((parsed_response or {}).get("evidence_excerpt")),
            "risk_flags": (parsed_response or {}).get("risk_flags", []),
            "needs_human_review": _needs_human_review(
                action=action,
                confidence=confidence or "UNKNOWN",
                parse_status=parse_status,
                validation_status=validation_status,
            ),
            "response_parse_status": parse_status,
            "response_validation_status": validation_status,
            "llm_mode": llm_mode,
            "llm_provider_env_source": runtime_config.env_source if runtime_config else "UNAVAILABLE",
            "llm_model": runtime_config.model if runtime_config else "",
            "prompt_version": PROMPT_VERSION,
            "prompt_hash": prompt_hash,
            "raw_response_hash": _response_hash(raw_content),
        }
        suggestion_rows.append(suggestion_row)

        response_audit_rows.append(
            {
                "alias_adjudication_id": alias_adjudication_id,
                "raw_metric_name": request_row["raw_metric_name"],
                "llm_mode": llm_mode,
                "response_parse_status": parse_status,
                "parse_method": parse_method,
                "response_validation_status": validation_status,
                "validation_errors": validation_errors,
                "needs_human_review": suggestion_row["needs_human_review"],
            }
        )
        if suggestion_row["needs_human_review"]:
            review_required_rows.append(dict(suggestion_row))

    map_to_existing_count = sum(
        1 for row in suggestion_rows if row.get("suggested_action") == "MAP_TO_EXISTING_STANDARD_METRIC"
    )
    propose_new_standard_count = sum(
        1 for row in suggestion_rows if row.get("suggested_action") == "PROPOSE_NEW_STANDARD_METRIC"
    )
    exclude_non_core_count = sum(
        1 for row in suggestion_rows if row.get("suggested_action") == "EXCLUDE_NON_CORE_METRIC"
    )
    needs_human_review_action_count = sum(
        1 for row in suggestion_rows if row.get("suggested_action") == "NEEDS_HUMAN_REVIEW"
    )
    insufficient_evidence_count = sum(
        1 for row in suggestion_rows if row.get("suggested_action") == "INSUFFICIENT_EVIDENCE"
    )
    high_confidence_suggestion_count = sum(1 for row in suggestion_rows if row.get("confidence") == "HIGH")
    medium_confidence_suggestion_count = sum(1 for row in suggestion_rows if row.get("confidence") == "MEDIUM")
    low_confidence_suggestion_count = sum(1 for row in suggestion_rows if row.get("confidence") == "LOW")
    parse_failed_count = sum(1 for row in suggestion_rows if row.get("response_parse_status") != "PARSED")
    validation_failed_count = sum(
        1 for row in suggestion_rows if row.get("response_validation_status") != "VALID"
    )

    input_hashes_after = {
        str(path): sha256_file(path)
        for path in [manifest_path, alias_queue_path, raw_metric_summary_path, metric_rows_path]
    }
    official_assets_after = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    protected_status_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged_after = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    qa_checks = [
        {
            "check": "input_manifest_exists",
            "passed": manifest_path.exists(),
        },
        {
            "check": "alias_queue_exists",
            "passed": alias_queue_path.exists(),
        },
        {
            "check": "request_package_generated",
            "passed": bool(request_rows),
        },
        {
            "check": "selected_count_respects_limit",
            "passed": len(selected_candidates) <= max_alias_candidates,
        },
        {
            "check": "no_write_back_to_345c_inputs",
            "passed": input_hashes_before == input_hashes_after,
        },
        {
            "check": "official_assets_unchanged",
            "passed": official_assets_before == official_assets_after,
        },
        {
            "check": "protected_dirty_status_unchanged",
            "passed": protected_status_before == protected_status_after,
        },
        {
            "check": "forbidden_paths_not_staged",
            "passed": forbidden_staged_before == forbidden_staged_after,
        },
        {
            "check": "formal_client_export_allowed_false",
            "passed": True,
        },
        {
            "check": "client_ready_false",
            "passed": True,
        },
        {
            "check": "production_ready_false",
            "passed": True,
        },
    ]
    qa_fail_count = sum(1 for row in qa_checks if not row["passed"])

    no_apply_proof = build_no_apply_proof(
        stage="345C2",
        files_read=[str(manifest_path), str(alias_queue_path), str(raw_metric_summary_path), str(metric_rows_path)],
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_proof_passed = (
        input_hashes_before == input_hashes_after
        and official_assets_before == official_assets_after
        and protected_status_before == protected_status_after
    )

    manifest = {
        "decision": _decision_for_mode(
            llm_mode=llm_mode,
            live_llm_suggestions_generated=live_llm_suggestions_generated,
            runtime_config_available=runtime_config_available,
        ),
        "input_stage": INPUT_STAGE,
        "qa_fail_count": qa_fail_count,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "llm_mode": llm_mode,
        "live_llm_suggestions_generated": live_llm_suggestions_generated,
        "runtime_config_available": runtime_config_available,
        "input_alias_candidate_count": len(alias_candidates),
        "selected_alias_candidate_count": len(selected_candidates),
        "suggestion_row_count": len(suggestion_rows),
        "map_to_existing_count": map_to_existing_count,
        "propose_new_standard_count": propose_new_standard_count,
        "exclude_non_core_count": exclude_non_core_count,
        "needs_human_review_count": len(review_required_rows),
        "insufficient_evidence_count": insufficient_evidence_count,
        "high_confidence_suggestion_count": high_confidence_suggestion_count,
        "medium_confidence_suggestion_count": medium_confidence_suggestion_count,
        "low_confidence_suggestion_count": low_confidence_suggestion_count,
        "parse_failed_count": parse_failed_count,
        "validation_failed_count": validation_failed_count,
        "request_package_generated": bool(request_rows),
        "alias_apply_simulation_ready": bool(suggestion_rows),
        "generated_at_utc": _utc_now(),
        "output_dir": str(output_dir),
    }
    response_audit = {
        "generated_at_utc": _utc_now(),
        "decision": manifest["decision"],
        "llm_mode": llm_mode,
        "runtime_config_available": runtime_config_available,
        "env_statuses": env_statuses,
        "response_rows": response_audit_rows,
        "qa_checks": qa_checks,
        "no_apply_proof": no_apply_proof,
        "input_hashes_before": input_hashes_before,
        "input_hashes_after": input_hashes_after,
    }

    return {
        "manifest": manifest,
        "alias_request_package_rows": request_rows,
        "alias_suggestion_rows": suggestion_rows,
        "review_required_rows": review_required_rows,
        "response_audit": response_audit,
        "artifact_index_rows": _artifact_rows(output_dir),
        "qa_checks": qa_checks,
    }
