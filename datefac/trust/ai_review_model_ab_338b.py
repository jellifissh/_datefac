from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

import pandas as pd
import requests

from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    capture_official_asset_hashes,
)


READY_DECISION = "AI_REVIEW_MODEL_AB_338B_READY"
PROMPTS_ONLY_DECISION = "AI_REVIEW_MODEL_AB_338B_PROMPTS_ONLY"
BLOCKED_MISSING_ENV_DECISION = "BLOCKED_MISSING_AI_REVIEW_ENV"
PARTIAL_DECISION = "AI_REVIEW_MODEL_AB_338B_PARTIAL"
BLOCKED_DECISION = "AI_REVIEW_MODEL_AB_338B_BLOCKED"

KEEP_DEEPSEEK_FLASH = "KEEP_DEEPSEEK_FLASH"
SWITCH_TO_AI_REVIEW_MODEL = "SWITCH_TO_AI_REVIEW_MODEL"
NEED_MORE_PRO_MODEL_TEST = "NEED_MORE_PRO_MODEL_TEST"
PROMPT_CONTEXT_STILL_TOO_WEAK = "PROMPT_CONTEXT_STILL_TOO_WEAK"

DEFAULT_BASELINE_338A_DIR = Path(r"D:\_datefac\output\deepseek_text_adjudicator_338a")
DEFAULT_REVIEWED_STRICTNESS_337D_DIR = Path(r"D:\_datefac\output\reviewed_strictness_year_alignment_337d")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\ai_review_model_ab_338b")
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
PERCENT_METRICS = {"ROE", "gross_margin", "net_margin", "revenue_yoy", "net_profit_yoy"}
MULTIPLE_METRICS = {"PE", "PB"}
YUAN_METRICS = {"EPS"}
AMOUNT_METRICS = {"revenue", "net_profit"}
MONEY_UNIT_KEYWORDS = ("百万元", "亿元", "万元", "千元", "元")
YEAR_RE = re.compile(r"(?:19|20)\d{2}[AE]?")
PROMPT_VERSION = "338B_v1"
LOW_CONFIDENCE_THRESHOLD = 0.70
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


def _contains_any(text: Any, patterns: Iterable[str]) -> bool:
    normalized = _norm_text(text).casefold()
    return any(pattern.casefold() in normalized for pattern in patterns)


def _is_money_unit(unit: str) -> bool:
    normalized = _norm_text(unit)
    return any(token in normalized for token in MONEY_UNIT_KEYWORDS)


def _normalize_unit(unit: Any) -> str:
    text = _norm_text(unit)
    if text.lower() == "x":
        return "倍"
    return text


def _decision_counts(frame: pd.DataFrame, column: str) -> Dict[str, int]:
    if frame.empty or column not in frame.columns:
        return {}
    counts: Dict[str, int] = {}
    for value in frame[column].tolist():
        key = _norm_text(value)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _extract_year_headers(table_preview: Any) -> List[str]:
    lines = [line.strip() for line in str(table_preview or "").splitlines() if line.strip()]
    seen = set()
    results: List[str] = []
    for line in lines[:2] or lines:
        for match in YEAR_RE.findall(line):
            if match not in seen:
                seen.add(match)
                results.append(match)
    return results


def _line_candidates_from_evidence(evidence: str, metric_before: str, metric_display_zh: str) -> List[str]:
    tokens: List[str] = []
    normalized_evidence = _norm_text(evidence)
    if normalized_evidence:
        tokens.append(normalized_evidence)
    if "|" in normalized_evidence:
        first_cell = _norm_text(normalized_evidence.split("|", 1)[0])
        if first_cell:
            tokens.append(first_cell)
    for token in (_norm_text(metric_display_zh), _norm_text(metric_before)):
        if token:
            tokens.append(token)
    deduped: List[str] = []
    seen = set()
    for token in tokens:
        if token not in seen:
            seen.add(token)
            deduped.append(token)
    return deduped


def _find_line_context(table_preview: Any, evidence: str, metric_before: str, metric_display_zh: str) -> Dict[str, str]:
    lines = [line.strip() for line in str(table_preview or "").splitlines() if line.strip()]
    if not lines:
        return {
            "matched_table_line": "",
            "previous_row": "",
            "next_row": "",
        }
    candidates = _line_candidates_from_evidence(evidence, metric_before, metric_display_zh)
    match_index = -1
    for index, line in enumerate(lines):
        if any(candidate and candidate in line for candidate in candidates):
            match_index = index
            break
    if match_index < 0:
        return {
            "matched_table_line": "",
            "previous_row": "",
            "next_row": "",
        }
    return {
        "matched_table_line": lines[match_index],
        "previous_row": lines[match_index - 1] if match_index > 0 else "",
        "next_row": lines[match_index + 1] if match_index + 1 < len(lines) else "",
    }


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

    def adjudicate(self, prompt: str) -> Dict[str, Any]:
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
                        "Use only the supplied text evidence. "
                        "Do not guess missing year/value mapping. "
                        "If context is insufficient, choose NEEDS_MORE_CONTEXT. "
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


def validate_evidence_quote(quote: Any, evidence: Any) -> bool:
    normalized_quote = _norm_text(quote).replace("...", "")
    normalized_evidence = _norm_text(evidence)
    if not normalized_quote:
        return False
    if normalized_quote in normalized_evidence:
        return True
    if len(normalized_quote) >= 6:
        for start in range(0, len(normalized_quote) - 5):
            if normalized_quote[start : start + 6] in normalized_evidence:
                return True
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


def _recommended_action(model_decision_status: str, model_decision: str, confidence: float, guard_result: str) -> Tuple[str, bool]:
    conflict = False
    if model_decision_status == "INVALID_RESPONSE":
        return "NEEDS_MORE_CONTEXT", False
    if guard_result != "PASS":
        if model_decision == "CONFIRM_REVIEWED":
            conflict = True
        if "LEGAL_RATING" in guard_result or "NON_REVIEWABLE_METADATA" in guard_result:
            return "REJECT", conflict
        return "DOWNGRADE_TO_NEEDS_REVIEW", conflict
    if confidence < LOW_CONFIDENCE_THRESHOLD:
        return "NEEDS_MORE_CONTEXT", False
    return model_decision or "NEEDS_MORE_CONTEXT", False


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


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_source_sheet_records(workbook_path: Path, sheet_name: str) -> Dict[int, Dict[str, Any]]:
    frame = _read_excel(workbook_path, sheet_name)
    records = frame.to_dict(orient="records")
    lookup: Dict[int, Dict[str, Any]] = {}
    if sheet_name == "02_NEEDS_REVIEW":
        for index, record in enumerate(records, start=2):
            key = _safe_int(record.get("row_no"), index)
            lookup[key] = dict(record)
    else:
        for index, record in enumerate(records, start=2):
            lookup[index] = dict(record)
    return lookup


def _build_table_context_lookup(table_summary_df: pd.DataFrame) -> Dict[str, List[Dict[str, Any]]]:
    by_document: Dict[str, List[Dict[str, Any]]] = {}
    for record in table_summary_df.to_dict(orient="records"):
        document = _norm_text(record.get("document"))
        by_document.setdefault(document, []).append(dict(record))
    return by_document


def _score_table_match(table_record: Mapping[str, Any], row: Mapping[str, Any]) -> int:
    preview = _norm_text(table_record.get("table_preview"))
    if not preview:
        return -999
    score = 0
    source_page = _norm_text(row.get("source_page"))
    page_no = _norm_text(table_record.get("page_no"))
    if source_page and page_no and source_page == page_no:
        score += 4
    evidence = _norm_text(row.get("evidence"))
    metric_before = _norm_text(row.get("metric_before"))
    metric_display_zh = _norm_text(row.get("metric_display_zh"))
    candidates = _line_candidates_from_evidence(evidence, metric_before, metric_display_zh)
    for candidate in candidates:
        if candidate and candidate in preview:
            score += 6 if candidate == evidence else 3
    years = {_norm_text(row.get("year_before")), _norm_text(row.get("suggested_year"))}
    for year in years:
        if year and year in preview:
            score += 1
    role = _norm_text(table_record.get("table_role_337c"))
    if role == "CORE_FINANCIAL_SUMMARY":
        score += 2
    elif role == "PROFIT_FORECAST_VALUATION":
        score += 1
    score += min(_safe_int(table_record.get("candidate_score"), 0), 30) // 10
    return score


def _match_table_context(row: Mapping[str, Any], table_lookup: Mapping[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    document = _norm_text(row.get("document"))
    candidates = list(table_lookup.get(document, []))
    if not candidates:
        return {
            "table_role_337d": "",
            "table_year_headers": [],
            "table_preview_excerpt": "",
            "matched_table_line": "",
            "previous_row": "",
            "next_row": "",
        }

    best = max(candidates, key=lambda candidate: _score_table_match(candidate, row))
    line_context = _find_line_context(
        best.get("table_preview"),
        _norm_text(row.get("evidence")),
        _norm_text(row.get("metric_before")),
        _norm_text(row.get("metric_display_zh")),
    )
    return {
        "table_role_337d": _norm_text(best.get("table_role_337c")),
        "table_year_headers": _extract_year_headers(best.get("table_preview")),
        "table_preview_excerpt": _truncate(best.get("table_preview"), MAX_CONTEXT_LEN),
        "matched_table_line": line_context["matched_table_line"],
        "previous_row": line_context["previous_row"],
        "next_row": line_context["next_row"],
    }


def _load_context_maps(reviewed_workbook_path: Path) -> Dict[str, Any]:
    source_records = {
        "08_SUSPICIOUS_REVIEWED_AUDIT": _load_source_sheet_records(reviewed_workbook_path, "08_SUSPICIOUS_REVIEWED_AUDIT"),
        "02_NEEDS_REVIEW": _load_source_sheet_records(reviewed_workbook_path, "02_NEEDS_REVIEW"),
    }
    table_summary_df = _read_excel(reviewed_workbook_path, "06_TABLE_CLASSIFICATION_SUMMARY")
    route_change_df = _read_excel(reviewed_workbook_path, "09_ROUTE_CHANGE_TRACE")

    route_map: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}
    for record in route_change_df.to_dict(orient="records"):
        key = (
            _norm_text(record.get("document")),
            _norm_text(record.get("metric_after_337d") or record.get("metric_before_337d")),
            _norm_text(record.get("year_after_337d") or record.get("year_before_337d")),
            _norm_text(record.get("source_evidence_excerpt")),
        )
        route_map[key] = dict(record)

    return {
        "source_records": source_records,
        "table_lookup": _build_table_context_lookup(table_summary_df),
        "route_map": route_map,
    }


def _build_row_context(base_row: Mapping[str, Any], context_maps: Mapping[str, Any]) -> Dict[str, Any]:
    source_sheet = _norm_text(base_row.get("source_sheet"))
    source_row_no = _safe_int(base_row.get("source_row_no"), 0)
    source_record = dict(context_maps["source_records"].get(source_sheet, {}).get(source_row_no, {}))

    route_key = (
        _norm_text(base_row.get("document")),
        _norm_text(base_row.get("metric_before")),
        _norm_text(base_row.get("year_before")),
        _norm_text(base_row.get("evidence")),
    )
    route_record = dict(context_maps["route_map"].get(route_key, {}))

    enriched: Dict[str, Any] = dict(base_row)
    if source_record:
        enriched["source_record"] = source_record
        if not enriched.get("source_page"):
            enriched["source_page"] = _norm_text(source_record.get("source_page"))
        if not enriched.get("evidence"):
            enriched["evidence"] = _norm_text(source_record.get("evidence") or source_record.get("source_evidence_excerpt"))
        if not enriched.get("notes"):
            enriched["notes"] = _norm_text(source_record.get("337d_action") or source_record.get("notes"))
    if route_record and not enriched.get("route_change_context"):
        enriched["route_change_context"] = " | ".join(
            [
                _norm_text(route_record.get("status_before_337d")),
                _norm_text(route_record.get("status_after_337d")),
                _norm_text(route_record.get("route_reason_before_337d")),
                _norm_text(route_record.get("route_reason_after_337d")),
                _norm_text(route_record.get("337d_action")),
                _norm_text(route_record.get("suspicious_reason")),
            ]
        ).strip(" |")

    table_context = _match_table_context(enriched, context_maps["table_lookup"])
    enriched.update(table_context)
    return enriched


def build_prompt_payload(row: Mapping[str, Any]) -> Dict[str, Any]:
    source_record = row.get("source_record") if isinstance(row.get("source_record"), dict) else {}
    return {
        "instruction": {
            "task": "Judge this row only from provided evidence and nearby table context.",
            "must_follow": [
                "Use only supplied text evidence.",
                "Do not guess missing year/value alignment.",
                "If headers are missing and mapping is not recoverable, choose NEEDS_MORE_CONTEXT.",
                "Return strict JSON only.",
                "The reason field must be short Chinese text.",
                "The evidence_quote must be copied from provided evidence only.",
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
                "evidence_quote": "short quote copied only from provided evidence",
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
            "route_change_context": _truncate(row.get("route_change_context"), MAX_CONTEXT_LEN),
            "deterministic_guard_result": _norm_text(row.get("deterministic_guard_result")),
            "table_role_from_337d": _norm_text(row.get("table_role_337d")),
            "table_year_headers": list(row.get("table_year_headers") or []),
            "matched_table_line": _norm_text(row.get("matched_table_line")),
            "nearby_previous_row": _norm_text(row.get("previous_row")),
            "nearby_next_row": _norm_text(row.get("next_row")),
            "table_preview_excerpt": _truncate(row.get("table_preview_excerpt"), MAX_CONTEXT_LEN),
            "original_row_evidence": _truncate(row.get("evidence"), MAX_EVIDENCE_LEN),
            "source_row_snapshot": {
                key: _truncate(value, 200)
                for key, value in source_record.items()
                if key
                in {
                    "candidate_id",
                    "document",
                    "metric",
                    "metric_display_zh",
                    "year",
                    "value",
                    "unit",
                    "source_page",
                    "evidence",
                    "source_evidence_excerpt",
                    "suspicious_reason",
                    "337d_action",
                    "notes",
                }
            },
        },
    }


def build_prompt_text(row: Mapping[str, Any]) -> str:
    payload = build_prompt_payload(row)
    return (
        "Please adjudicate the row from text evidence only.\n"
        "Do not use outside knowledge.\n"
        "Do not guess missing year mappings.\n"
        "If the evidence cannot support a confident judgment, return NEEDS_MORE_CONTEXT.\n\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def _validate_model_output(parsed: Dict[str, Any] | None, evidence: str) -> Tuple[Dict[str, Any], str, List[str], bool]:
    errors: List[str] = []
    if parsed is None:
        return {}, "INVALID_RESPONSE", ["json_parse_failed"], False

    decision = _norm_text(parsed.get("decision"))
    if decision not in ALLOWED_MODEL_DECISIONS:
        errors.append("invalid_decision")
    table_role_guess = _norm_text(parsed.get("table_role_guess"))
    if table_role_guess not in ALLOWED_TABLE_ROLES:
        errors.append("invalid_table_role_guess")
    try:
        confidence = float(parsed.get("confidence"))
        if confidence < 0 or confidence > 1:
            errors.append("confidence_out_of_range")
    except Exception:
        errors.append("confidence_not_numeric")
    risk_flags = parsed.get("risk_flags")
    if not isinstance(risk_flags, list):
        errors.append("risk_flags_not_list")

    evidence_quote = _norm_text(parsed.get("evidence_quote"))
    quote_valid = validate_evidence_quote(evidence_quote, evidence)
    if not quote_valid:
        errors.append("evidence_quote_not_grounded")

    status = "VALID" if not errors else "INVALID_RESPONSE"
    return parsed, status, errors, quote_valid


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
        "evidence_quote": _truncate(evidence, 40),
    }
    return json.dumps(payload, ensure_ascii=False)


def _build_recommendation(metrics: Mapping[str, Any]) -> str:
    baseline_invalid = _safe_int(metrics.get("invalid_response_count_baseline"))
    new_invalid = _safe_int(metrics.get("invalid_response_count_new"))
    baseline_low = _safe_int(metrics.get("low_confidence_count_baseline"))
    new_low = _safe_int(metrics.get("low_confidence_count_new"))
    baseline_nmc = _safe_int(metrics.get("needs_more_context_count_baseline"))
    new_nmc = _safe_int(metrics.get("needs_more_context_count_new"))
    baseline_conflicts = _safe_int(metrics.get("rule_model_conflict_count_baseline"))
    new_conflicts = _safe_int(metrics.get("rule_model_conflict_count_new"))
    evidence_invalid = _safe_int(metrics.get("evidence_quote_invalid_count"))
    decision_changed = _safe_int(metrics.get("decision_changed_count"))
    prompt_year_header_hit_count = _safe_int(metrics.get("prompt_year_header_hit_count"))
    row_count = max(_safe_int(metrics.get("row_count")), 1)

    if new_invalid > baseline_invalid or evidence_invalid > 0 or new_conflicts > baseline_conflicts:
        return NEED_MORE_PRO_MODEL_TEST
    if prompt_year_header_hit_count < row_count // 4 and new_nmc >= baseline_nmc:
        return PROMPT_CONTEXT_STILL_TOO_WEAK
    materially_better = (
        new_low <= max(baseline_low - 5, 0)
        and new_nmc <= max(baseline_nmc - 5, 0)
        and decision_changed > 0
    )
    if materially_better:
        return SWITCH_TO_AI_REVIEW_MODEL
    if new_low >= baseline_low and new_nmc >= baseline_nmc:
        return KEEP_DEEPSEEK_FLASH
    return NEED_MORE_PRO_MODEL_TEST


def _customer_readme_df() -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "topic": "Workbook purpose",
                    "message": "This workbook compares the new AI review model against the 338A DeepSeek flash baseline on the same rows.",
                },
                {
                    "topic": "Boundaries",
                    "message": "This remains a sidecar dry run. No write-back is performed to 337D or any production asset.",
                },
                {
                    "topic": "Prompt upgrade",
                    "message": "338B adds year headers, nearby rows, table role hints, source page, suspicious reason, and deterministic guard context.",
                },
            ]
        )
    )


def build_ai_review_model_ab_338b(
    *,
    baseline_338a_dir: Path,
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

    baseline_summary_path = baseline_338a_dir / "deepseek_text_adjudicator_338a_summary.json"
    baseline_workbook_path = baseline_338a_dir / "deepseek_text_adjudication_plan_338a.xlsx"
    reviewed_workbook_path = reviewed_strictness_337d_dir / "real_test_mineru_client_export_337d.xlsx"
    reviewed_before_after_path = reviewed_strictness_337d_dir / "reviewed_strictness_year_alignment_337d_before_after.xlsx"
    reviewed_summary_path = reviewed_strictness_337d_dir / "reviewed_strictness_year_alignment_337d_summary.json"

    blocked_reasons: List[str] = []
    for path in [
        baseline_summary_path,
        baseline_workbook_path,
        reviewed_workbook_path,
        reviewed_before_after_path,
        reviewed_summary_path,
    ]:
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

    baseline_summary = _read_json(baseline_summary_path)
    reviewed_summary = _read_json(reviewed_summary_path)
    baseline_plan_df = _read_excel(baseline_workbook_path, "02_MODEL_ADJUDICATION_PLAN").head(max(1, int(limit)))
    context_maps = _load_context_maps(reviewed_workbook_path)

    cache_path = output_dir / "ai_review_model_ab_338b_cache.jsonl"
    existing_cache = _load_cache(cache_path)
    cache_rows_map: Dict[str, Dict[str, Any]] = dict(existing_cache)

    prompt_preview_rows: List[Dict[str, Any]] = []
    new_plan_rows: List[Dict[str, Any]] = []
    comparison_rows: List[Dict[str, Any]] = []
    changed_rows: List[Dict[str, Any]] = []
    invalid_or_low_rows: List[Dict[str, Any]] = []
    conflict_rows: List[Dict[str, Any]] = []
    prompt_context_rows: List[Dict[str, Any]] = []

    api_call_count = 0
    cache_hit_count = 0
    invalid_response_count_new = 0
    low_confidence_count_new = 0
    rule_model_conflict_count_new = 0
    evidence_quote_valid_count = 0
    evidence_quote_invalid_count = 0
    prompt_year_header_hit_count = 0

    for base_row in baseline_plan_df.to_dict(orient="records"):
        row = _build_row_context(base_row, context_maps)
        row["deterministic_guard_result"] = _norm_text(base_row.get("deterministic_guard_result")) or deterministic_guard(row, {})
        prompt_payload = build_prompt_payload(row)
        prompt_text = build_prompt_text(row)
        cache_key = build_cache_key(prompt_payload)
        prompt_sha = prompt_hash(prompt_text)

        if row.get("table_year_headers"):
            prompt_year_header_hit_count += 1

        prompt_preview_rows.append(
            {
                "adjudication_id": _norm_text(row.get("adjudication_id")),
                "document": _norm_text(row.get("document")),
                "source_sheet": _norm_text(row.get("source_sheet")),
                "source_row_no": _safe_int(row.get("source_row_no"), 0),
                "model_name": runtime_config.model if runtime_config else "",
                "prompt_hash": prompt_sha,
                "prompt_text": prompt_text,
            }
        )

        prompt_context_rows.append(
            {
                "adjudication_id": _norm_text(row.get("adjudication_id")),
                "document": _norm_text(row.get("document")),
                "source_sheet": _norm_text(row.get("source_sheet")),
                "source_row_no": _safe_int(row.get("source_row_no"), 0),
                "table_role_337d": _norm_text(row.get("table_role_337d")),
                "table_year_headers": " | ".join(row.get("table_year_headers") or []),
                "matched_table_line": _norm_text(row.get("matched_table_line")),
                "nearby_previous_row": _norm_text(row.get("previous_row")),
                "nearby_next_row": _norm_text(row.get("next_row")),
                "source_page": _norm_text(row.get("source_page")),
                "suspicious_reason": _norm_text(row.get("suspicious_reason")),
                "deterministic_guard_result": _norm_text(row.get("deterministic_guard_result")),
                "route_change_context": _truncate(row.get("route_change_context"), MAX_CONTEXT_LEN),
            }
        )

        raw_content = ""
        parse_method = "not_run"
        raw_response_obj: Dict[str, Any] = {}
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
                raw_response_obj = call_result.get("raw_response") or {}
            except Exception as exc:
                raw_content = _build_error_fallback(exc, _norm_text(row.get("evidence")))
                raw_response_obj = {"error": str(exc)}
            parsed_for_cache, parse_method = parse_model_json(raw_content)
            cache_rows_map[cache_key] = {
                "cache_key": cache_key,
                "adjudication_id": _norm_text(row.get("adjudication_id")),
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

        parsed_response, model_decision_status, validation_errors, evidence_quote_valid = _validate_model_output(
            parsed_response,
            _norm_text(row.get("evidence")),
        )
        model_decision = _norm_text(parsed_response.get("decision")) if parsed_response else ""
        confidence = _safe_float(parsed_response.get("confidence")) if parsed_response else 0.0
        guard_result = deterministic_guard(row, parsed_response or {})
        recommended_final_action, has_conflict = _recommended_action(
            model_decision_status=model_decision_status if (parsed_response or raw_content) else "INVALID_RESPONSE",
            model_decision=model_decision,
            confidence=confidence,
            guard_result=guard_result,
        )

        if model_decision_status == "INVALID_RESPONSE":
            invalid_response_count_new += 1
        elif confidence < LOW_CONFIDENCE_THRESHOLD:
            low_confidence_count_new += 1

        if has_conflict:
            rule_model_conflict_count_new += 1

        if evidence_quote_valid:
            evidence_quote_valid_count += 1
        else:
            evidence_quote_invalid_count += 1

        status_label = model_decision_status
        if dry_run_prompts_only:
            status_label = "NOT_RUN"
        elif not api_env_ready:
            status_label = BLOCKED_MISSING_ENV_DECISION

        new_plan_row = {
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
            "evidence": _truncate(row.get("evidence"), MAX_EVIDENCE_LEN),
            "suspicious_reason": _norm_text(row.get("suspicious_reason")),
            "notes": _norm_text(row.get("notes")),
            "route_change_context": _truncate(row.get("route_change_context"), MAX_CONTEXT_LEN),
            "table_role_337d": _norm_text(row.get("table_role_337d")),
            "table_year_headers": " | ".join(row.get("table_year_headers") or []),
            "matched_table_line": _norm_text(row.get("matched_table_line")),
            "nearby_previous_row": _norm_text(row.get("previous_row")),
            "nearby_next_row": _norm_text(row.get("next_row")),
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
            "evidence_quote": _norm_text(parsed_response.get("evidence_quote")) if parsed_response else "",
            "evidence_quote_grounded": evidence_quote_valid,
            "deterministic_guard_result": guard_result,
            "recommended_final_action": recommended_final_action if (parsed_response or raw_content or dry_run_prompts_only or not api_env_ready) else "NEEDS_MORE_CONTEXT",
            "model_name": runtime_config.model if runtime_config else "",
            "prompt_hash": prompt_sha,
            "cache_hit": cache_hit,
            "parse_method": parse_method,
            "validation_errors": "|".join(validation_errors),
        }
        new_plan_rows.append(new_plan_row)

        baseline_final = _norm_text(base_row.get("recommended_final_action"))
        comparison_row = {
            "adjudication_id": _norm_text(row.get("adjudication_id")),
            "document": _norm_text(row.get("document")),
            "source_sheet": _norm_text(row.get("source_sheet")),
            "source_row_no": _safe_int(row.get("source_row_no"), 0),
            "baseline_model_name": _norm_text(base_row.get("model_name")),
            "new_model_name": runtime_config.model if runtime_config else "",
            "metric_before": _norm_text(row.get("metric_before")),
            "year_before": _norm_text(row.get("year_before")),
            "value_before": _norm_text(row.get("value_before")),
            "unit_before": _norm_text(row.get("unit_before")),
            "baseline_model_decision": _norm_text(base_row.get("model_decision")),
            "new_model_decision": _norm_text(new_plan_row.get("model_decision")),
            "baseline_final_action": baseline_final,
            "new_final_action": _norm_text(new_plan_row.get("recommended_final_action")),
            "baseline_confidence": _safe_float(base_row.get("confidence")),
            "new_confidence": confidence,
            "baseline_guard_result": _norm_text(base_row.get("deterministic_guard_result")),
            "new_guard_result": guard_result,
            "decision_changed": baseline_final != _norm_text(new_plan_row.get("recommended_final_action")),
            "evidence_quote_grounded": evidence_quote_valid,
        }
        comparison_rows.append(comparison_row)

        if comparison_row["decision_changed"]:
            changed_rows.append(comparison_row)
        if status_label == "INVALID_RESPONSE" or confidence < LOW_CONFIDENCE_THRESHOLD:
            invalid_or_low_rows.append(new_plan_row)
        if has_conflict:
            conflict_rows.append(new_plan_row)

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_status_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)
    protected_cached_after = _git_cached_names_for_paths(PROTECTED_DIRTY_PATHS)

    new_plan_df = _clean_frame(pd.DataFrame(new_plan_rows))
    baseline_trimmed_df = _clean_frame(baseline_plan_df.copy())
    comparison_df = _clean_frame(pd.DataFrame(comparison_rows))
    changed_df = _clean_frame(pd.DataFrame(changed_rows))
    invalid_or_low_df = _clean_frame(pd.DataFrame(invalid_or_low_rows))
    conflict_df = _clean_frame(pd.DataFrame(conflict_rows))
    prompt_context_df = _clean_frame(pd.DataFrame(prompt_context_rows))

    new_counts = _decision_counts(new_plan_df, "recommended_final_action")
    baseline_counts = _decision_counts(baseline_trimmed_df, "recommended_final_action")
    decision_changed_count = int(comparison_df["decision_changed"].sum()) if not comparison_df.empty else 0

    comparison_metrics = {
        "baseline_model_name": _norm_text(baseline_summary.get("model_name")),
        "new_model_name": runtime_config.model if runtime_config else "",
        "row_count": len(new_plan_df),
        "invalid_response_count_baseline": _safe_int(baseline_summary.get("invalid_response_count")),
        "invalid_response_count_new": invalid_response_count_new,
        "low_confidence_count_baseline": _safe_int(baseline_summary.get("low_confidence_count")),
        "low_confidence_count_new": low_confidence_count_new,
        "needs_more_context_count_baseline": baseline_counts.get("NEEDS_MORE_CONTEXT", 0),
        "needs_more_context_count_new": new_counts.get("NEEDS_MORE_CONTEXT", 0),
        "confirm_reviewed_count_baseline": baseline_counts.get("CONFIRM_REVIEWED", 0),
        "confirm_reviewed_count_new": new_counts.get("CONFIRM_REVIEWED", 0),
        "downgrade_count_baseline": baseline_counts.get("DOWNGRADE_TO_NEEDS_REVIEW", 0),
        "downgrade_count_new": new_counts.get("DOWNGRADE_TO_NEEDS_REVIEW", 0),
        "reject_count_baseline": baseline_counts.get("REJECT", 0),
        "reject_count_new": new_counts.get("REJECT", 0),
        "rule_model_conflict_count_baseline": _safe_int(baseline_summary.get("rule_model_conflict_count")),
        "rule_model_conflict_count_new": rule_model_conflict_count_new,
        "decision_changed_count": decision_changed_count,
        "evidence_quote_valid_count": evidence_quote_valid_count,
        "evidence_quote_invalid_count": evidence_quote_invalid_count,
        "prompt_year_header_hit_count": prompt_year_header_hit_count,
    }
    recommendation = _build_recommendation(comparison_metrics)

    if dry_run_prompts_only:
        decision = PROMPTS_ONLY_DECISION
    elif not api_env_ready:
        decision = BLOCKED_MISSING_ENV_DECISION
    else:
        decision = READY_DECISION

    qa_checks = [
        {
            "check_name": "baseline_338a_plan_exists",
            "status": "PASS" if baseline_workbook_path.exists() else "FAIL",
            "detail": str(baseline_workbook_path),
        },
        {
            "check_name": "reviewed_337d_workbook_exists",
            "status": "PASS" if reviewed_workbook_path.exists() else "FAIL",
            "detail": str(reviewed_workbook_path),
        },
        {
            "check_name": "row_count_matches_baseline",
            "status": "PASS" if len(new_plan_df) == len(baseline_trimmed_df) else "FAIL",
            "detail": f"{len(new_plan_df)} / {len(baseline_trimmed_df)}",
        },
        {
            "check_name": "prompt_preview_generated",
            "status": "PASS" if len(prompt_preview_rows) == len(baseline_trimmed_df) else "FAIL",
            "detail": f"{len(prompt_preview_rows)} / {len(baseline_trimmed_df)}",
        },
        {
            "check_name": "official_assets_unchanged",
            "status": "PASS" if official_assets_before == official_assets_after else "FAIL",
            "detail": json.dumps(official_assets_after, ensure_ascii=False),
        },
        {
            "check_name": "protected_dirty_status_preserved",
            "status": "PASS" if protected_status_before == protected_status_after else "FAIL",
            "detail": json.dumps(protected_status_after, ensure_ascii=False),
        },
        {
            "check_name": "protected_dirty_paths_not_staged",
            "status": "PASS" if not protected_cached_after else "FAIL",
            "detail": json.dumps(protected_cached_after, ensure_ascii=False),
        },
        {
            "check_name": "reviewed_summary_ready",
            "status": "PASS" if _norm_text(reviewed_summary.get("decision")) == "REVIEWED_STRICTNESS_YEAR_ALIGNMENT_337D_READY" else "FAIL",
            "detail": _norm_text(reviewed_summary.get("decision")),
        },
    ]
    qa_fail_count = sum(1 for check in qa_checks if check["status"] == "FAIL")
    if qa_fail_count and decision == READY_DECISION:
        decision = PARTIAL_DECISION

    summary = {
        "generated_at_utc": _utc_now(),
        "client_ready": False,
        "production_ready": False,
        "baseline_338a_dir": str(baseline_338a_dir),
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
        "baseline_model_name": comparison_metrics["baseline_model_name"],
        "new_model_name": comparison_metrics["new_model_name"],
        "row_count": comparison_metrics["row_count"],
        "api_call_count": api_call_count,
        "cache_hit_count": cache_hit_count,
        "invalid_response_count_baseline": comparison_metrics["invalid_response_count_baseline"],
        "invalid_response_count_new": comparison_metrics["invalid_response_count_new"],
        "low_confidence_count_baseline": comparison_metrics["low_confidence_count_baseline"],
        "low_confidence_count_new": comparison_metrics["low_confidence_count_new"],
        "needs_more_context_count_baseline": comparison_metrics["needs_more_context_count_baseline"],
        "needs_more_context_count_new": comparison_metrics["needs_more_context_count_new"],
        "confirm_reviewed_count_baseline": comparison_metrics["confirm_reviewed_count_baseline"],
        "confirm_reviewed_count_new": comparison_metrics["confirm_reviewed_count_new"],
        "downgrade_count_baseline": comparison_metrics["downgrade_count_baseline"],
        "downgrade_count_new": comparison_metrics["downgrade_count_new"],
        "reject_count_baseline": comparison_metrics["reject_count_baseline"],
        "reject_count_new": comparison_metrics["reject_count_new"],
        "rule_model_conflict_count_new": comparison_metrics["rule_model_conflict_count_new"],
        "decision_changed_count": comparison_metrics["decision_changed_count"],
        "evidence_quote_valid_count": comparison_metrics["evidence_quote_valid_count"],
        "evidence_quote_invalid_count": comparison_metrics["evidence_quote_invalid_count"],
        "prompt_year_header_hit_count": comparison_metrics["prompt_year_header_hit_count"],
        "recommendation": recommendation,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
    }

    manifest = {
        "task": "338B_ai_review_model_adapter_ab_evaluation",
        "baseline_338a_dir": str(baseline_338a_dir),
        "reviewed_strictness_337d_dir": str(reviewed_strictness_337d_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / "ai_review_model_ab_338b_summary.json"),
            "manifest_json": str(output_dir / "ai_review_model_ab_338b_manifest.json"),
            "qa_json": str(output_dir / "ai_review_model_ab_338b_qa.json"),
            "report_md": str(output_dir / "ai_review_model_ab_338b_report.md"),
            "plan_xlsx": str(output_dir / "ai_review_model_ab_338b_plan.xlsx"),
            "cache_jsonl": str(output_dir / "ai_review_model_ab_338b_cache.jsonl"),
            "prompt_preview_jsonl": str(output_dir / "ai_review_model_ab_338b_prompt_preview.jsonl"),
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

    ab_summary_df = _clean_frame(pd.DataFrame([summary]))
    cache_cost_df = _clean_frame(
        pd.DataFrame(
            [
                {
                    "env_source": runtime_config.env_source if runtime_config else "",
                    "new_model_name": runtime_config.model if runtime_config else "",
                    "api_env_ready": api_env_ready,
                    "dry_run_prompts_only": dry_run_prompts_only,
                    "row_count": len(new_plan_df),
                    "api_call_count": api_call_count,
                    "cache_hit_count": cache_hit_count,
                    "cache_write_count": max(len(cache_rows_map) - len(existing_cache), 0),
                }
            ]
        )
    )

    workbook_sheets = {
        "00_README": _customer_readme_df(),
        "01_AB_SUMMARY": ab_summary_df,
        "02_NEW_MODEL_ADJUDICATION_PLAN": new_plan_df,
        "03_DEEPSEEK_338A_BASELINE": baseline_trimmed_df,
        "04_ROW_LEVEL_COMPARISON": comparison_df,
        "05_CHANGED_DECISIONS": changed_df,
        "06_INVALID_OR_LOW_CONFIDENCE": invalid_or_low_df,
        "07_RULE_MODEL_CONFLICTS": conflict_df,
        "08_PROMPT_CONTEXT_UPGRADE": prompt_context_df,
        "09_CACHE_AND_COST_SUMMARY": cache_cost_df,
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "workbook_sheets": workbook_sheets,
        "prompt_preview_rows": prompt_preview_rows,
        "cache_rows": list(cache_rows_map.values()),
    }
