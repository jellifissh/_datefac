from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import pandas as pd
import requests

from datefac.llm.client import ChatCompletionsClient
from datefac.llm.config import resolve_ai_review_runtime_config
from datefac.llm.json_utils import parse_model_json as shared_parse_model_json

from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    capture_official_asset_hashes,
)


READY_DECISION = "GROUNDED_AI_REVIEW_338C_READY"
PROMPTS_ONLY_DECISION = "GROUNDED_AI_REVIEW_338C_PROMPTS_ONLY"
BLOCKED_MISSING_ENV_DECISION = "BLOCKED_MISSING_AI_REVIEW_ENV"
PARTIAL_DECISION = "GROUNDED_AI_REVIEW_338C_PARTIAL"
BLOCKED_DECISION = "GROUNDED_AI_REVIEW_338C_BLOCKED"

SWITCH_TO_AI_REVIEW_MODEL = "SWITCH_TO_AI_REVIEW_MODEL"
KEEP_DEEPSEEK_FLASH = "KEEP_DEEPSEEK_FLASH"
NEED_MORE_PRO_MODEL_TEST = "NEED_MORE_PRO_MODEL_TEST"
GROUNDING_STILL_TOO_WEAK = "GROUNDING_STILL_TOO_WEAK"
PROMPT_CONTEXT_STILL_TOO_WEAK = "PROMPT_CONTEXT_STILL_TOO_WEAK"

DEFAULT_AB_338B_DIR = Path(r"D:\_datefac\output\ai_review_model_ab_338b")
DEFAULT_REVIEWED_STRICTNESS_337D_DIR = Path(r"D:\_datefac\output\reviewed_strictness_year_alignment_337d")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\grounded_ai_review_338c")
DEFAULT_LIMIT = 50
DEFAULT_TIMEOUT_SECONDS = 60
PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "temp",
]

ALLOWED_MODEL_DECISIONS = {
    "CONFIRM_REVIEWED",
    "DOWNGRADE_TO_NEEDS_REVIEW",
    "REJECT",
    "NEEDS_MORE_CONTEXT",
}
ALLOWED_TABLE_ROLES = {
    "CORE_FINANCIAL_SUMMARY",
    "PROFIT_FORECAST_VALUATION",
    "FINANCIAL_STATEMENT_DETAIL",
    "INDUSTRY_DATA_TABLE",
    "RATING_STANDARD_TABLE",
    "LEGAL_DISCLOSURE_TABLE",
    "COMPANY_PROFILE_TABLE",
    "OTHER_TABLE",
    "UNKNOWN",
}
ALLOWED_GROUNDING_SOURCES = {
    "RAW_EVIDENCE",
    "SUPPORTING_CONTEXT",
    "BOTH",
    "INSUFFICIENT",
}
PERCENT_METRICS = {"ROE", "gross_margin", "net_margin", "revenue_yoy", "net_profit_yoy"}
MULTIPLE_METRICS = {"PE", "PB"}
YUAN_METRICS = {"EPS"}
AMOUNT_METRICS = {"revenue", "net_profit"}
MONEY_UNIT_KEYWORDS = ("百万元", "亿元", "万元", "千元", "元")
LOW_CONFIDENCE_THRESHOLD = 0.70
CONFIRM_CONFIDENCE_THRESHOLD = 0.80
PROMPT_VERSION = "338C_v1"
MAX_EVIDENCE_LEN = 800
MAX_CONTEXT_LEN = 500


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return re.sub(r"\s+", " ", str(value).strip())


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _truncate(text: Any, limit: int) -> str:
    normalized = _norm_text(text)
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."


def _git_status_porcelain_for_paths(paths: Sequence[str]) -> List[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.rstrip() for line in result.stdout.splitlines() if line.strip()]


def _git_cached_names_for_paths(paths: Sequence[str]) -> List[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", *paths],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _read_excel(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return _clean_frame(pd.read_excel(path, sheet_name=sheet_name))


def _normalize_unit(unit: Any) -> str:
    text = _norm_text(unit)
    if text.lower() == "x":
        return "倍"
    return text


def _is_money_unit(unit: Any) -> bool:
    normalized = _norm_text(unit)
    return any(token in normalized for token in MONEY_UNIT_KEYWORDS)


def _decision_counts(frame: pd.DataFrame, column: str) -> Dict[str, int]:
    if frame.empty or column not in frame.columns:
        return {}
    counts: Dict[str, int] = {}
    for value in frame[column].tolist():
        key = _norm_text(value)
        counts[key] = counts.get(key, 0) + 1
    return counts


@dataclass
class AIReviewRuntimeConfig:
    api_key: str
    base_url: str
    model: str
    env_source: str
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS


class AIReviewTextClient:
    def __init__(self, config: AIReviewRuntimeConfig) -> None:
        self.config = config
        self._client = ChatCompletionsClient(
            config=config,
            system_prompt=(
                "You are a strict Chinese financial-text adjudicator. "
                "You may use supporting context, but you must separate raw evidence quotes from supporting context quotes. "
                "Do not invent any quote. "
                "If raw evidence and context conflict, choose NEEDS_MORE_CONTEXT. "
                "Return JSON only."
            ),
            temperature=0,
            response_format={"type": "json_object"},
        )

    def adjudicate(self, prompt: str) -> Dict[str, Any]:
        return self._client.adjudicate(prompt)
        endpoint = self.config.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.config.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a strict Chinese financial-text adjudicator. "
                        "You may use supporting context, but you must separate raw evidence quotes from supporting context quotes. "
                        "Do not invent any quote. "
                        "If raw evidence and context conflict, choose NEEDS_MORE_CONTEXT. "
                        "Return JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }
        response = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        content = ""
        if isinstance(data, dict):
            choices = data.get("choices", [])
            if choices:
                content = _norm_text(choices[0].get("message", {}).get("content"))
        return {"raw_response": data, "content": content}


def resolve_runtime_config(env: Mapping[str, str] | None = None, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> Tuple[AIReviewRuntimeConfig | None, Dict[str, str]]:
    runtime_config, statuses = resolve_ai_review_runtime_config(env=env or os.environ, timeout_seconds=timeout_seconds)
    if runtime_config is not None:
        return (
            AIReviewRuntimeConfig(
                api_key=runtime_config.api_key,
                base_url=runtime_config.base_url,
                model=runtime_config.model,
                env_source=runtime_config.env_source,
                timeout_seconds=runtime_config.timeout_seconds,
            ),
            statuses,
        )
    source_env = dict(env or os.environ)
    statuses = {
        "AI_REVIEW_API_KEY": "SET" if _norm_text(source_env.get("AI_REVIEW_API_KEY")) else "MISSING",
        "AI_REVIEW_BASE_URL": "SET" if _norm_text(source_env.get("AI_REVIEW_BASE_URL")) else "MISSING",
        "AI_MODEL": "SET" if _norm_text(source_env.get("AI_MODEL")) else "MISSING",
        "DEEPSEEK_API_KEY": "SET" if _norm_text(source_env.get("DEEPSEEK_API_KEY")) else "MISSING",
        "DEEPSEEK_BASE_URL": "SET" if _norm_text(source_env.get("DEEPSEEK_BASE_URL")) else "MISSING",
        "DEEPSEEK_MODEL": "SET" if _norm_text(source_env.get("DEEPSEEK_MODEL")) else "MISSING",
    }
    preferred = (
        _norm_text(source_env.get("AI_REVIEW_API_KEY")),
        _norm_text(source_env.get("AI_REVIEW_BASE_URL")),
        _norm_text(source_env.get("AI_MODEL")),
    )
    if all(preferred):
        return (
            AIReviewRuntimeConfig(
                api_key=preferred[0],
                base_url=preferred[1],
                model=preferred[2],
                env_source="AI_REVIEW",
                timeout_seconds=timeout_seconds,
            ),
            statuses,
        )

    fallback = (
        _norm_text(source_env.get("DEEPSEEK_API_KEY")),
        _norm_text(source_env.get("DEEPSEEK_BASE_URL")),
        _norm_text(source_env.get("DEEPSEEK_MODEL")),
    )
    if all(fallback):
        return (
            AIReviewRuntimeConfig(
                api_key=fallback[0],
                base_url=fallback[1],
                model=fallback[2],
                env_source="DEEPSEEK_FALLBACK",
                timeout_seconds=timeout_seconds,
            ),
            statuses,
        )
    return None, statuses


def parse_model_json(text: str) -> Tuple[Dict[str, Any] | None, str]:
    return shared_parse_model_json(_norm_text(text))
    cleaned = _norm_text(text)
    if not cleaned:
        return None, "empty_response"
    try:
        return json.loads(cleaned), "raw_json"
    except Exception:
        pass
    if "```" in cleaned:
        for block in cleaned.split("```"):
            candidate = block.strip()
            if candidate.startswith("json"):
                candidate = candidate[4:].strip()
            if candidate.startswith("{") and candidate.endswith("}"):
                try:
                    return json.loads(candidate), "fence_repair"
                except Exception:
                    continue
    left = cleaned.find("{")
    right = cleaned.rfind("}")
    if left >= 0 and right > left:
        candidate = cleaned[left : right + 1]
        try:
            return json.loads(candidate), "bracket_repair"
        except Exception:
            return None, "json_parse_failed"
    return None, "json_parse_failed"


def validate_quote_against_text(quote: Any, source_text: Any) -> bool:
    normalized_quote = _norm_text(quote).replace("...", "")
    normalized_source = _norm_text(source_text)
    if not normalized_quote:
        return False
    if normalized_quote in normalized_source:
        return True
    if len(normalized_quote) >= 6:
        for start in range(0, len(normalized_quote) - 5):
            if normalized_quote[start : start + 6] in normalized_source:
                return True
    return False


def validate_grounding_source(
    grounding_source: str,
    *,
    raw_quote_valid: bool,
    context_quote_valid: bool,
) -> bool:
    if grounding_source == "RAW_EVIDENCE":
        return raw_quote_valid
    if grounding_source == "SUPPORTING_CONTEXT":
        return context_quote_valid
    if grounding_source == "BOTH":
        return raw_quote_valid and context_quote_valid
    if grounding_source == "INSUFFICIENT":
        return not raw_quote_valid and not context_quote_valid
    return False


def deterministic_guard(row: Mapping[str, Any], model_output: Mapping[str, Any]) -> str:
    metric = _norm_text(model_output.get("suggested_metric") or row.get("metric_before"))
    value = _norm_text(model_output.get("suggested_value") or row.get("value_before"))
    unit = _normalize_unit(model_output.get("suggested_unit") or row.get("unit_before"))
    table_role = _norm_text(model_output.get("table_role_guess") or row.get("table_role_337d"))
    source_sheet = _norm_text(row.get("source_sheet"))
    notes = _norm_text(row.get("notes"))

    if table_role in {"LEGAL_DISCLOSURE_TABLE", "RATING_STANDARD_TABLE"}:
        return "HARD_REJECT_LEGAL_RATING"
    if source_sheet == "02_NEEDS_REVIEW" and "metric_not_allowed_for_reviewed" in notes:
        return "HARD_REJECT_NON_REVIEWABLE_METADATA"
    if metric in AMOUNT_METRICS and ("%" in value or unit == "%"):
        return "HARD_REJECT_PERCENT_AS_AMOUNT"
    if metric in AMOUNT_METRICS and not _is_money_unit(unit):
        return "HARD_REJECT_MISSING_MONEY_UNIT"
    if metric in MULTIPLE_METRICS and unit not in {"倍", "x", "X"}:
        return "HARD_REJECT_WRONG_MULTIPLE_UNIT"
    if metric in YUAN_METRICS and unit != "元":
        return "HARD_REJECT_WRONG_EPS_UNIT"
    if metric in PERCENT_METRICS and unit != "%":
        return "HARD_REJECT_WRONG_PERCENT_UNIT"
    return "PASS"


def _supporting_context_text(row: Mapping[str, Any]) -> str:
    return " | ".join(
        [
            _norm_text(row.get("table_year_headers")),
            _norm_text(row.get("matched_table_line")),
            _norm_text(row.get("nearby_previous_row")),
            _norm_text(row.get("nearby_next_row")),
            _norm_text(row.get("route_change_context")),
        ]
    ).strip(" |")


def _row_fields_agree_for_confirm(row: Mapping[str, Any], model_output: Mapping[str, Any]) -> bool:
    return (
        _norm_text(model_output.get("suggested_metric")) in {"", _norm_text(row.get("metric_before"))}
        and _norm_text(model_output.get("suggested_year")) in {"", _norm_text(row.get("year_before"))}
        and _norm_text(model_output.get("suggested_value")) in {"", _norm_text(row.get("value_before"))}
        and _normalize_unit(model_output.get("suggested_unit")) in {"", _normalize_unit(row.get("unit_before"))}
    )


def _recommended_action(
    *,
    row: Mapping[str, Any],
    model_decision_status: str,
    model_decision: str,
    confidence: float,
    guard_result: str,
    grounding_source: str,
    raw_quote_valid: bool,
    context_quote_valid: bool,
) -> Tuple[str, bool, bool]:
    conflict = False
    rejected_by_grounding = False
    if model_decision_status == "INVALID_RESPONSE":
        return "NEEDS_MORE_CONTEXT", False, False
    if guard_result != "PASS":
        if model_decision == "CONFIRM_REVIEWED":
            conflict = True
        if "LEGAL_RATING" in guard_result or "NON_REVIEWABLE_METADATA" in guard_result:
            return "REJECT", conflict, False
        return "DOWNGRADE_TO_NEEDS_REVIEW", conflict, False
    if confidence < LOW_CONFIDENCE_THRESHOLD:
        return "NEEDS_MORE_CONTEXT", False, False
    if model_decision != "CONFIRM_REVIEWED":
        return model_decision or "NEEDS_MORE_CONTEXT", False, False

    accepted_grounding = grounding_source in {"RAW_EVIDENCE", "BOTH"}
    if confidence < CONFIRM_CONFIDENCE_THRESHOLD or not accepted_grounding or not raw_quote_valid:
        rejected_by_grounding = True
        return "NEEDS_MORE_CONTEXT", False, rejected_by_grounding
    if grounding_source == "SUPPORTING_CONTEXT":
        if _row_fields_agree_for_confirm(row, row):
            return "NEEDS_MORE_CONTEXT", False, True
        return "NEEDS_MORE_CONTEXT", False, True
    if not validate_grounding_source(grounding_source, raw_quote_valid=raw_quote_valid, context_quote_valid=context_quote_valid):
        return "NEEDS_MORE_CONTEXT", False, True
    return "CONFIRM_REVIEWED", False, False


def _load_cache(path: Path) -> Dict[str, Dict[str, Any]]:
    cache: Dict[str, Dict[str, Any]] = {}
    if not path.exists():
        return cache
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        key = _norm_text(row.get("cache_key"))
        if key:
            cache[key] = row
    return cache


def build_cache_key(prompt_payload: Mapping[str, Any]) -> str:
    serialized = json.dumps(prompt_payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def prompt_hash(prompt_text: str) -> str:
    return hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()


def build_prompt_payload(row: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "instruction": {
            "task": "Judge this row using raw evidence first and supporting context second.",
            "must_follow": [
                "Return strict JSON only.",
                "Do not invent quotes.",
                "raw_evidence_quote must come only from original evidence.",
                "supporting_context_quote must come only from supporting context.",
                "If raw evidence and context conflict, choose NEEDS_MORE_CONTEXT.",
                "Do not provide investment advice.",
            ],
            "required_json_schema": {
                "decision": "CONFIRM_REVIEWED | DOWNGRADE_TO_NEEDS_REVIEW | REJECT | NEEDS_MORE_CONTEXT",
                "suggested_metric": "string_or_null",
                "suggested_year": "string_or_null",
                "suggested_value": "string_or_null",
                "suggested_unit": "string_or_null",
                "table_role_guess": "CORE_FINANCIAL_SUMMARY | PROFIT_FORECAST_VALUATION | FINANCIAL_STATEMENT_DETAIL | INDUSTRY_DATA_TABLE | RATING_STANDARD_TABLE | LEGAL_DISCLOSURE_TABLE | COMPANY_PROFILE_TABLE | OTHER_TABLE | UNKNOWN",
                "risk_flags": ["string"],
                "confidence": 0.0,
                "reason": "short Chinese explanation",
                "raw_evidence_quote": "short quote copied only from the original evidence field",
                "supporting_context_quote": "short quote copied only from the provided supporting context, or null",
                "grounding_source": "RAW_EVIDENCE | SUPPORTING_CONTEXT | BOTH | INSUFFICIENT",
            },
        },
        "row": {
            "adjudication_id": _norm_text(row.get("adjudication_id")),
            "document": _norm_text(row.get("document")),
            "source_sheet": _norm_text(row.get("source_sheet")),
            "source_row_no": _safe_int(row.get("source_row_no"), 0),
            "metric_before": _norm_text(row.get("metric_before")),
            "metric_display_zh": _norm_text(row.get("metric_display_zh")),
            "year_before": _norm_text(row.get("year_before")),
            "value_before": _norm_text(row.get("value_before")),
            "unit_before": _norm_text(row.get("unit_before")),
            "source_page": _norm_text(row.get("source_page")),
            "status_before": _norm_text(row.get("status_before")),
            "suspicious_reason": _norm_text(row.get("suspicious_reason")),
            "notes": _norm_text(row.get("notes")),
            "deterministic_guard_result": _norm_text(row.get("deterministic_guard_result")),
            "table_role_from_337d": _norm_text(row.get("table_role_337d")),
            "original_evidence": _truncate(row.get("evidence"), MAX_EVIDENCE_LEN),
            "supporting_context": {
                "table_year_headers": _norm_text(row.get("table_year_headers")),
                "matched_table_line": _norm_text(row.get("matched_table_line")),
                "nearby_previous_row": _norm_text(row.get("nearby_previous_row")),
                "nearby_next_row": _norm_text(row.get("nearby_next_row")),
                "route_change_context": _truncate(row.get("route_change_context"), MAX_CONTEXT_LEN),
            },
        },
    }


def build_prompt_text(row: Mapping[str, Any]) -> str:
    payload = build_prompt_payload(row)
    return (
        "Please adjudicate this row using raw evidence first and supporting context second.\n"
        "Do not mix supporting context into raw_evidence_quote.\n"
        "If the row cannot be grounded by the provided evidence, prefer NEEDS_MORE_CONTEXT.\n\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def _build_error_fallback(exc: Exception, evidence: str) -> str:
    payload = {
        "decision": "NEEDS_MORE_CONTEXT",
        "suggested_metric": None,
        "suggested_year": None,
        "suggested_value": None,
        "suggested_unit": None,
        "table_role_guess": "UNKNOWN",
        "risk_flags": ["api_error"],
        "confidence": 0.0,
        "reason": f"接口异常:{_truncate(str(exc), 80)}",
        "raw_evidence_quote": _truncate(evidence, 40),
        "supporting_context_quote": None,
        "grounding_source": "INSUFFICIENT",
    }
    return json.dumps(payload, ensure_ascii=False)


def _validate_model_output(parsed: Dict[str, Any] | None, row: Mapping[str, Any]) -> Tuple[Dict[str, Any], str, List[str], bool, bool]:
    errors: List[str] = []
    if parsed is None:
        return {}, "INVALID_RESPONSE", ["json_parse_failed"], False, False

    decision = _norm_text(parsed.get("decision"))
    if decision not in ALLOWED_MODEL_DECISIONS:
        errors.append("invalid_decision")
    table_role_guess = _norm_text(parsed.get("table_role_guess"))
    if table_role_guess not in ALLOWED_TABLE_ROLES:
        errors.append("invalid_table_role_guess")
    grounding_source = _norm_text(parsed.get("grounding_source"))
    if grounding_source not in ALLOWED_GROUNDING_SOURCES:
        errors.append("invalid_grounding_source")
    try:
        confidence = float(parsed.get("confidence"))
        if confidence < 0 or confidence > 1:
            errors.append("confidence_out_of_range")
    except Exception:
        errors.append("confidence_not_numeric")
    risk_flags = parsed.get("risk_flags")
    if not isinstance(risk_flags, list):
        errors.append("risk_flags_not_list")

    raw_quote_valid = validate_quote_against_text(parsed.get("raw_evidence_quote"), row.get("evidence")) if _norm_text(parsed.get("raw_evidence_quote")) else False
    context_quote_valid = validate_quote_against_text(parsed.get("supporting_context_quote"), _supporting_context_text(row)) if _norm_text(parsed.get("supporting_context_quote")) else False
    if _norm_text(parsed.get("raw_evidence_quote")) and not raw_quote_valid:
        errors.append("raw_evidence_quote_not_grounded")
    if _norm_text(parsed.get("supporting_context_quote")) and not context_quote_valid:
        errors.append("supporting_context_quote_not_grounded")
    if grounding_source and not validate_grounding_source(grounding_source, raw_quote_valid=raw_quote_valid, context_quote_valid=context_quote_valid):
        errors.append("grounding_source_mismatch")
    if decision == "CONFIRM_REVIEWED" and grounding_source not in {"RAW_EVIDENCE", "BOTH"}:
        errors.append("confirm_not_grounded_in_raw_evidence")

    status = "VALID" if not errors else "INVALID_RESPONSE"
    return parsed, status, errors, raw_quote_valid, context_quote_valid


def _load_context_maps(reviewed_workbook_path: Path) -> Tuple[Dict[Tuple[str, int], Dict[str, Any]], Dict[Tuple[str, str, int], Dict[str, Any]]]:
    plan_df = _read_excel(reviewed_workbook_path, "08_PROMPT_CONTEXT_UPGRADE")
    plan_map: Dict[Tuple[str, int], Dict[str, Any]] = {}
    for record in plan_df.to_dict(orient="records"):
        plan_map[(_norm_text(record.get("source_sheet")), _safe_int(record.get("source_row_no"), 0))] = dict(record)

    source_df = _read_excel(reviewed_workbook_path, "02_NEW_MODEL_ADJUDICATION_PLAN")
    source_map: Dict[Tuple[str, str, int], Dict[str, Any]] = {}
    for record in source_df.to_dict(orient="records"):
        key = (
            _norm_text(record.get("adjudication_id")),
            _norm_text(record.get("source_sheet")),
            _safe_int(record.get("source_row_no"), 0),
        )
        source_map[key] = dict(record)
    return plan_map, source_map


def _build_recommendation(metrics: Mapping[str, Any]) -> str:
    invalid_338c = _safe_int(metrics.get("invalid_response_count_338c"))
    invalid_338b = _safe_int(metrics.get("invalid_response_count_338b"))
    confirm_context_only = _safe_int(metrics.get("confirm_with_context_only_count"))
    confirm_rejected_by_grounding = _safe_int(metrics.get("confirm_rejected_by_grounding_count"))
    raw_valid = _safe_int(metrics.get("raw_quote_valid_count"))
    row_count = max(_safe_int(metrics.get("row_count")), 1)
    nmc_338b = _safe_int(metrics.get("needs_more_context_count_338b"))
    nmc_338c = _safe_int(metrics.get("needs_more_context_count_338c"))
    conflict_count = _safe_int(metrics.get("rule_model_conflict_count"))

    if invalid_338c > max(1, invalid_338b) or confirm_context_only > 0:
        return GROUNDING_STILL_TOO_WEAK
    if raw_valid < row_count * 0.6:
        return GROUNDING_STILL_TOO_WEAK
    if confirm_rejected_by_grounding > 5:
        return GROUNDING_STILL_TOO_WEAK
    if nmc_338c >= nmc_338b and row_count > 0:
        return PROMPT_CONTEXT_STILL_TOO_WEAK
    if invalid_338c == 0 and conflict_count == 0 and nmc_338c < nmc_338b:
        return SWITCH_TO_AI_REVIEW_MODEL
    if invalid_338c <= 1 and conflict_count == 0 and nmc_338c <= nmc_338b:
        return NEED_MORE_PRO_MODEL_TEST
    return KEEP_DEEPSEEK_FLASH


def _customer_readme_df() -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "topic": "Workbook purpose",
                    "message": "This workbook tightens quote grounding by separating raw evidence quotes from supporting context quotes.",
                },
                {
                    "topic": "Boundary",
                    "message": "338C remains sidecar dry-run only and does not write back to 337D or any production asset.",
                },
                {
                    "topic": "Adoption gate",
                    "message": "Accepted confirm rows must be grounded in RAW_EVIDENCE or BOTH, pass deterministic guards, and reach the higher confidence threshold.",
                },
            ]
        )
    )


def build_grounded_ai_review_338c(
    *,
    ab_338b_dir: Path,
    reviewed_strictness_337d_dir: Path,
    output_dir: Path,
    limit: int = DEFAULT_LIMIT,
    dry_run_prompts_only: bool = False,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    client: AIReviewTextClient | None = None,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
    env: Mapping[str, str] | None = None,
) -> Dict[str, Any]:
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_status_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)

    summary_338b_path = ab_338b_dir / "ai_review_model_ab_338b_summary.json"
    plan_338b_path = ab_338b_dir / "ai_review_model_ab_338b_plan.xlsx"
    reviewed_workbook_path = reviewed_strictness_337d_dir / "real_test_mineru_client_export_337d.xlsx"
    reviewed_before_after_path = reviewed_strictness_337d_dir / "reviewed_strictness_year_alignment_337d_before_after.xlsx"
    reviewed_summary_path = reviewed_strictness_337d_dir / "reviewed_strictness_year_alignment_337d_summary.json"

    blocked_reasons: List[str] = []
    for path in [summary_338b_path, plan_338b_path, reviewed_workbook_path, reviewed_before_after_path, reviewed_summary_path]:
        if not path.exists():
            blocked_reasons.append(f"Missing required input: {path}")
    if blocked_reasons:
        summary = {
            "generated_at_utc": _utc_now(),
            "client_ready": False,
            "production_ready": False,
            "qa_fail_count": len(blocked_reasons),
            "decision": BLOCKED_DECISION,
        }
        return {
            "summary": summary,
            "manifest": {},
            "qa_json": {
                "decision": BLOCKED_DECISION,
                "qa_fail_count": len(blocked_reasons),
                "checks": [],
                "blocked_reasons": blocked_reasons,
            },
            "workbook_sheets": {},
            "prompt_preview_rows": [],
            "cache_rows": [],
        }

    runtime_config, env_statuses = resolve_runtime_config(env=env, timeout_seconds=timeout_seconds)
    api_env_ready = runtime_config is not None
    if client is None and api_env_ready and not dry_run_prompts_only:
        client = AIReviewTextClient(runtime_config)

    summary_338b = json.loads(summary_338b_path.read_text(encoding="utf-8"))
    reviewed_summary = json.loads(reviewed_summary_path.read_text(encoding="utf-8"))
    source_plan_df = _read_excel(plan_338b_path, "02_NEW_MODEL_ADJUDICATION_PLAN").head(max(1, int(limit)))
    plan_context_map, source_map = _load_context_maps(plan_338b_path)

    cache_path = output_dir / "grounded_ai_review_338c_cache.jsonl"
    existing_cache = _load_cache(cache_path)
    cache_rows_map: Dict[str, Dict[str, Any]] = dict(existing_cache)

    prompt_preview_rows: List[Dict[str, Any]] = []
    grounded_rows: List[Dict[str, Any]] = []
    comparison_rows: List[Dict[str, Any]] = []
    changed_rows: List[Dict[str, Any]] = []
    invalid_rows: List[Dict[str, Any]] = []
    confirm_rows: List[Dict[str, Any]] = []
    needs_more_context_rows: List[Dict[str, Any]] = []
    conflict_rows: List[Dict[str, Any]] = []
    notes_rows: List[Dict[str, Any]] = []

    api_call_count = 0
    cache_hit_count = 0
    invalid_response_count_338c = 0
    rule_model_conflict_count = 0
    raw_quote_valid_count = 0
    context_quote_valid_count = 0
    confirm_with_raw_evidence_count = 0
    confirm_with_both_count = 0
    confirm_with_context_only_count = 0
    confirm_rejected_by_grounding_count = 0
    grounding_source_counter: Dict[str, int] = {}

    for row in source_plan_df.to_dict(orient="records"):
        source_key = (
            _norm_text(row.get("adjudication_id")),
            _norm_text(row.get("source_sheet")),
            _safe_int(row.get("source_row_no"), 0),
        )
        original_row = dict(source_map.get(source_key, {}))
        plan_context = dict(plan_context_map.get((_norm_text(row.get("source_sheet")), _safe_int(row.get("source_row_no"), 0)), {}))
        merged_row = dict(row)
        merged_row.update(plan_context)
        if original_row:
            merged_row["evidence"] = _norm_text(original_row.get("evidence") or row.get("evidence"))
        prompt_payload = build_prompt_payload(merged_row)
        prompt_text = build_prompt_text(merged_row)
        cache_key = build_cache_key(prompt_payload)
        prompt_sha = prompt_hash(prompt_text)

        prompt_preview_rows.append(
            {
                "adjudication_id": _norm_text(merged_row.get("adjudication_id")),
                "document": _norm_text(merged_row.get("document")),
                "source_sheet": _norm_text(merged_row.get("source_sheet")),
                "source_row_no": _safe_int(merged_row.get("source_row_no"), 0),
                "model_name": runtime_config.model if runtime_config else "",
                "prompt_hash": prompt_sha,
                "prompt_text": prompt_text,
            }
        )

        notes_rows.append(
            {
                "adjudication_id": _norm_text(merged_row.get("adjudication_id")),
                "document": _norm_text(merged_row.get("document")),
                "raw_evidence": _norm_text(merged_row.get("evidence")),
                "supporting_context": _supporting_context_text(merged_row),
                "schema_note": "raw_evidence_quote must come from raw evidence only; supporting_context_quote must come from expanded context only.",
            }
        )

        raw_content = ""
        parse_method = "not_run"
        cache_hit = False
        if cache_key in cache_rows_map:
            cache_entry = cache_rows_map[cache_key]
            raw_content = _norm_text(cache_entry.get("raw_content"))
            parse_method = _norm_text(cache_entry.get("parse_method")) or "cache"
            cache_hit = True
            cache_hit_count += 1
        elif dry_run_prompts_only or not api_env_ready or client is None:
            parse_method = "prompts_only" if dry_run_prompts_only else "missing_runtime"
        else:
            api_call_count += 1
            try:
                call_result = client.adjudicate(prompt_text)
                raw_content = _norm_text(call_result.get("content"))
            except Exception as exc:
                raw_content = _build_error_fallback(exc, _norm_text(merged_row.get("evidence")))
            parsed_for_cache, parse_method = parse_model_json(raw_content)
            cache_rows_map[cache_key] = {
                "cache_key": cache_key,
                "adjudication_id": _norm_text(merged_row.get("adjudication_id")),
                "prompt_hash": prompt_sha,
                "model_name": runtime_config.model if runtime_config else "",
                "raw_content": raw_content,
                "parsed_response": parsed_for_cache,
                "parse_method": parse_method,
                "cached_at_utc": _utc_now(),
            }

        parsed_response = None
        if cache_hit:
            parsed_response = cache_rows_map[cache_key].get("parsed_response")
        elif raw_content:
            parsed_response, parse_method = parse_model_json(raw_content)

        parsed_response, model_decision_status, validation_errors, raw_quote_valid, context_quote_valid = _validate_model_output(parsed_response, merged_row)
        model_decision = _norm_text(parsed_response.get("decision")) if parsed_response else ""
        confidence = _safe_float(parsed_response.get("confidence")) if parsed_response else 0.0
        guard_result = deterministic_guard(merged_row, parsed_response or {})
        grounding_source = _norm_text(parsed_response.get("grounding_source")) if parsed_response else ""
        recommended_final_action, has_conflict, rejected_by_grounding = _recommended_action(
            row=merged_row,
            model_decision_status=model_decision_status if (parsed_response or raw_content) else "INVALID_RESPONSE",
            model_decision=model_decision,
            confidence=confidence,
            guard_result=guard_result,
            grounding_source=grounding_source,
            raw_quote_valid=raw_quote_valid,
            context_quote_valid=context_quote_valid,
        )

        if raw_quote_valid:
            raw_quote_valid_count += 1
        if context_quote_valid:
            context_quote_valid_count += 1
        if model_decision_status == "INVALID_RESPONSE":
            invalid_response_count_338c += 1
        if has_conflict:
            rule_model_conflict_count += 1
        if rejected_by_grounding:
            confirm_rejected_by_grounding_count += 1

        if grounding_source:
            grounding_source_counter[grounding_source] = grounding_source_counter.get(grounding_source, 0) + 1

        if model_decision == "CONFIRM_REVIEWED":
            if grounding_source == "RAW_EVIDENCE":
                confirm_with_raw_evidence_count += 1
            elif grounding_source == "BOTH":
                confirm_with_both_count += 1
            elif grounding_source == "SUPPORTING_CONTEXT":
                confirm_with_context_only_count += 1

        status_label = model_decision_status
        if dry_run_prompts_only:
            status_label = "NOT_RUN"
        elif not api_env_ready:
            status_label = BLOCKED_MISSING_ENV_DECISION

        grounded_row = {
            "adjudication_id": _norm_text(merged_row.get("adjudication_id")),
            "document": _norm_text(merged_row.get("document")),
            "source_sheet": _norm_text(merged_row.get("source_sheet")),
            "source_row_no": _safe_int(merged_row.get("source_row_no"), 0),
            "metric_before": _norm_text(merged_row.get("metric_before")),
            "metric_display_zh": _norm_text(merged_row.get("metric_display_zh")),
            "year_before": _norm_text(merged_row.get("year_before")),
            "value_before": _norm_text(merged_row.get("value_before")),
            "unit_before": _norm_text(merged_row.get("unit_before")),
            "source_page": _norm_text(merged_row.get("source_page")),
            "status_before": _norm_text(merged_row.get("status_before")),
            "evidence": _truncate(merged_row.get("evidence"), MAX_EVIDENCE_LEN),
            "suspicious_reason": _norm_text(merged_row.get("suspicious_reason")),
            "notes": _norm_text(merged_row.get("notes")),
            "route_change_context": _truncate(merged_row.get("route_change_context"), MAX_CONTEXT_LEN),
            "table_role_337d": _norm_text(merged_row.get("table_role_337d")),
            "table_year_headers": _norm_text(merged_row.get("table_year_headers")),
            "matched_table_line": _norm_text(merged_row.get("matched_table_line")),
            "nearby_previous_row": _norm_text(merged_row.get("nearby_previous_row")),
            "nearby_next_row": _norm_text(merged_row.get("nearby_next_row")),
            "model_decision_status": status_label,
            "model_decision": model_decision or ("NEEDS_MORE_CONTEXT" if status_label == "INVALID_RESPONSE" else ""),
            "suggested_metric": _norm_text(parsed_response.get("suggested_metric")) if parsed_response else "",
            "suggested_year": _norm_text(parsed_response.get("suggested_year")) if parsed_response else "",
            "suggested_value": _norm_text(parsed_response.get("suggested_value")) if parsed_response else "",
            "suggested_unit": _norm_text(parsed_response.get("suggested_unit")) if parsed_response else "",
            "table_role_guess": _norm_text(parsed_response.get("table_role_guess")) if parsed_response else "",
            "confidence": confidence,
            "risk_flags": "|".join(parsed_response.get("risk_flags", [])) if parsed_response and isinstance(parsed_response.get("risk_flags"), list) else "",
            "reason": _norm_text(parsed_response.get("reason")) if parsed_response else "",
            "raw_evidence_quote": _norm_text(parsed_response.get("raw_evidence_quote")) if parsed_response else "",
            "supporting_context_quote": _norm_text(parsed_response.get("supporting_context_quote")) if parsed_response else "",
            "grounding_source": grounding_source,
            "raw_quote_valid": raw_quote_valid,
            "context_quote_valid": context_quote_valid,
            "deterministic_guard_result": guard_result,
            "recommended_final_action": recommended_final_action,
            "confirm_rejected_by_grounding": rejected_by_grounding,
            "model_name": runtime_config.model if runtime_config else "",
            "prompt_hash": prompt_sha,
            "cache_hit": cache_hit,
            "parse_method": parse_method,
            "validation_errors": "|".join(validation_errors),
        }
        grounded_rows.append(grounded_row)

        previous_final = _norm_text(row.get("recommended_final_action"))
        comparison_row = {
            "adjudication_id": _norm_text(merged_row.get("adjudication_id")),
            "document": _norm_text(merged_row.get("document")),
            "source_sheet": _norm_text(merged_row.get("source_sheet")),
            "source_row_no": _safe_int(merged_row.get("source_row_no"), 0),
            "final_action_338b": previous_final,
            "final_action_338c": _norm_text(grounded_row.get("recommended_final_action")),
            "model_decision_338b": _norm_text(row.get("model_decision")),
            "model_decision_338c": _norm_text(grounded_row.get("model_decision")),
            "invalid_338b": _norm_text(row.get("model_decision_status")) == "INVALID_RESPONSE",
            "invalid_338c": status_label == "INVALID_RESPONSE",
            "grounding_source_338c": grounding_source,
            "decision_changed_after_grounding": previous_final != _norm_text(grounded_row.get("recommended_final_action")),
        }
        comparison_rows.append(comparison_row)

        if comparison_row["decision_changed_after_grounding"]:
            changed_rows.append(comparison_row)
        if status_label == "INVALID_RESPONSE" or rejected_by_grounding:
            invalid_rows.append(grounded_row)
        if grounded_row["recommended_final_action"] == "CONFIRM_REVIEWED":
            confirm_rows.append(grounded_row)
        if grounded_row["recommended_final_action"] == "NEEDS_MORE_CONTEXT":
            needs_more_context_rows.append(grounded_row)
        if has_conflict:
            conflict_rows.append(grounded_row)

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_status_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)
    protected_cached_after = _git_cached_names_for_paths(PROTECTED_DIRTY_PATHS)

    grounded_df = _clean_frame(pd.DataFrame(grounded_rows))
    comparison_df = _clean_frame(pd.DataFrame(comparison_rows))
    changed_df = _clean_frame(pd.DataFrame(changed_rows))
    invalid_df = _clean_frame(pd.DataFrame(invalid_rows))
    confirm_df = _clean_frame(pd.DataFrame(confirm_rows))
    needs_more_context_df = _clean_frame(pd.DataFrame(needs_more_context_rows))
    conflict_df = _clean_frame(pd.DataFrame(conflict_rows))
    notes_df = _clean_frame(pd.DataFrame(notes_rows))

    counts_338c = _decision_counts(grounded_df, "recommended_final_action")
    counts_338b = _decision_counts(source_plan_df, "recommended_final_action")
    grounding_source_counts = dict(sorted(grounding_source_counter.items()))
    final_recommendation = _build_recommendation(
        {
            "row_count": len(grounded_df),
            "invalid_response_count_338b": _safe_int(summary_338b.get("invalid_response_count_new")),
            "invalid_response_count_338c": invalid_response_count_338c,
            "needs_more_context_count_338b": counts_338b.get("NEEDS_MORE_CONTEXT", 0),
            "needs_more_context_count_338c": counts_338c.get("NEEDS_MORE_CONTEXT", 0),
            "raw_quote_valid_count": raw_quote_valid_count,
            "confirm_with_context_only_count": confirm_with_context_only_count,
            "confirm_rejected_by_grounding_count": confirm_rejected_by_grounding_count,
            "rule_model_conflict_count": rule_model_conflict_count,
        }
    )

    if dry_run_prompts_only:
        decision = PROMPTS_ONLY_DECISION
    elif not api_env_ready:
        decision = BLOCKED_MISSING_ENV_DECISION
    else:
        decision = READY_DECISION

    qa_checks = [
        {"check_name": "ab_338b_plan_exists", "status": "PASS" if plan_338b_path.exists() else "FAIL", "detail": str(plan_338b_path)},
        {"check_name": "reviewed_337d_workbook_exists", "status": "PASS" if reviewed_workbook_path.exists() else "FAIL", "detail": str(reviewed_workbook_path)},
        {"check_name": "row_count_matches_338b", "status": "PASS" if len(grounded_df) == len(source_plan_df) else "FAIL", "detail": f"{len(grounded_df)} / {len(source_plan_df)}"},
        {"check_name": "prompt_preview_generated", "status": "PASS" if len(prompt_preview_rows) == len(source_plan_df) else "FAIL", "detail": f"{len(prompt_preview_rows)} / {len(source_plan_df)}"},
        {"check_name": "official_assets_unchanged", "status": "PASS" if official_assets_before == official_assets_after else "FAIL", "detail": json.dumps(official_assets_after, ensure_ascii=False)},
        {"check_name": "protected_dirty_status_preserved", "status": "PASS" if protected_status_before == protected_status_after else "FAIL", "detail": json.dumps(protected_status_after, ensure_ascii=False)},
        {"check_name": "protected_dirty_paths_not_staged", "status": "PASS" if not protected_cached_after else "FAIL", "detail": json.dumps(protected_cached_after, ensure_ascii=False)},
        {"check_name": "reviewed_summary_ready", "status": "PASS" if _norm_text(reviewed_summary.get("decision")) == "REVIEWED_STRICTNESS_YEAR_ALIGNMENT_337D_READY" else "FAIL", "detail": _norm_text(reviewed_summary.get("decision"))},
    ]
    qa_fail_count = sum(1 for check in qa_checks if check["status"] == "FAIL")
    if qa_fail_count and decision == READY_DECISION:
        decision = PARTIAL_DECISION

    summary = {
        "generated_at_utc": _utc_now(),
        "client_ready": False,
        "production_ready": False,
        "ab_338b_dir": str(ab_338b_dir),
        "reviewed_strictness_337d_dir": str(reviewed_strictness_337d_dir),
        "output_dir": str(output_dir),
        "env_source": runtime_config.env_source if runtime_config else "",
        "AI_REVIEW_API_KEY": env_statuses["AI_REVIEW_API_KEY"],
        "AI_REVIEW_BASE_URL": env_statuses["AI_REVIEW_BASE_URL"],
        "AI_MODEL": env_statuses["AI_MODEL"],
        "DEEPSEEK_API_KEY": env_statuses["DEEPSEEK_API_KEY"],
        "DEEPSEEK_BASE_URL": env_statuses["DEEPSEEK_BASE_URL"],
        "DEEPSEEK_MODEL": env_statuses["DEEPSEEK_MODEL"],
        "api_env_ready": api_env_ready,
        "dry_run_prompts_only": dry_run_prompts_only,
        "model_name": runtime_config.model if runtime_config else "",
        "row_count": len(grounded_df),
        "api_call_count": api_call_count,
        "cache_hit_count": cache_hit_count,
        "invalid_response_count_338b": _safe_int(summary_338b.get("invalid_response_count_new")),
        "invalid_response_count_338c": invalid_response_count_338c,
        "confirm_reviewed_count_338b": counts_338b.get("CONFIRM_REVIEWED", 0),
        "confirm_reviewed_count_338c": counts_338c.get("CONFIRM_REVIEWED", 0),
        "needs_more_context_count_338b": counts_338b.get("NEEDS_MORE_CONTEXT", 0),
        "needs_more_context_count_338c": counts_338c.get("NEEDS_MORE_CONTEXT", 0),
        "raw_quote_valid_count": raw_quote_valid_count,
        "context_quote_valid_count": context_quote_valid_count,
        "grounding_source_counts": grounding_source_counts,
        "confirm_with_raw_evidence_count": confirm_with_raw_evidence_count,
        "confirm_with_both_count": confirm_with_both_count,
        "confirm_with_context_only_count": confirm_with_context_only_count,
        "confirm_rejected_by_grounding_count": confirm_rejected_by_grounding_count,
        "rule_model_conflict_count": rule_model_conflict_count,
        "final_recommendation": final_recommendation,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
    }

    manifest = {
        "task": "338C_grounded_ai_review_schema_tightening",
        "ab_338b_dir": str(ab_338b_dir),
        "reviewed_strictness_337d_dir": str(reviewed_strictness_337d_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / "grounded_ai_review_338c_summary.json"),
            "manifest_json": str(output_dir / "grounded_ai_review_338c_manifest.json"),
            "qa_json": str(output_dir / "grounded_ai_review_338c_qa.json"),
            "report_md": str(output_dir / "grounded_ai_review_338c_report.md"),
            "plan_xlsx": str(output_dir / "grounded_ai_review_338c_plan.xlsx"),
            "cache_jsonl": str(output_dir / "grounded_ai_review_338c_cache.jsonl"),
            "prompt_preview_jsonl": str(output_dir / "grounded_ai_review_338c_prompt_preview.jsonl"),
        },
    }

    qa_json = {
        "decision": decision,
        "qa_fail_count": qa_fail_count,
        "checks": qa_checks,
        "blocked_reasons": blocked_reasons,
        "official_assets_before": official_assets_before,
        "official_assets_after": official_assets_after,
    }

    summary_df = _clean_frame(pd.DataFrame([summary]))
    cache_cost_df = _clean_frame(
        pd.DataFrame(
            [
                {
                    "env_source": runtime_config.env_source if runtime_config else "",
                    "model_name": runtime_config.model if runtime_config else "",
                    "api_env_ready": api_env_ready,
                    "dry_run_prompts_only": dry_run_prompts_only,
                    "row_count": len(grounded_df),
                    "api_call_count": api_call_count,
                    "cache_hit_count": cache_hit_count,
                    "cache_write_count": max(len(cache_rows_map) - len(existing_cache), 0),
                }
            ]
        )
    )

    workbook_sheets = {
        "00_README": _customer_readme_df(),
        "01_GROUNDED_SUMMARY": summary_df,
        "02_GROUNDED_ADJUDICATION_PLAN": grounded_df,
        "03_338B_COMPARISON": comparison_df,
        "04_CHANGED_AFTER_GROUNDING": changed_df,
        "05_INVALID_OR_UNGROUNDED": invalid_df,
        "06_CONFIRM_REVIEWED_CANDIDATES": confirm_df,
        "07_NEEDS_MORE_CONTEXT_AFTER_GROUNDING": needs_more_context_df,
        "08_RULE_MODEL_CONFLICTS": conflict_df,
        "09_PROMPT_AND_SCHEMA_NOTES": notes_df,
        "10_CACHE_AND_COST_SUMMARY": cache_cost_df,
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "workbook_sheets": workbook_sheets,
        "prompt_preview_rows": prompt_preview_rows,
        "cache_rows": list(cache_rows_map.values()),
    }
