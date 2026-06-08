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


READY_DECISION = "DEEPSEEK_TEXT_ADJUDICATOR_338A_READY"
PROMPTS_ONLY_DECISION = "DEEPSEEK_TEXT_ADJUDICATOR_338A_PROMPTS_ONLY"
BLOCKED_MISSING_KEY_DECISION = "BLOCKED_MISSING_DEEPSEEK_API_KEY"
PARTIAL_DECISION = "DEEPSEEK_TEXT_ADJUDICATOR_338A_PARTIAL"
BLOCKED_DECISION = "DEEPSEEK_TEXT_ADJUDICATOR_338A_BLOCKED"

DEFAULT_REVIEWED_STRICTNESS_337D_DIR = Path(r"D:\_datefac\output\reviewed_strictness_year_alignment_337d")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\deepseek_text_adjudicator_338a")
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_LIMIT = 50
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
PROMPT_VERSION = "338A_v1"
MAX_EVIDENCE_LEN = 600
MAX_CONTEXT_LEN = 400


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


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


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


def _is_money_unit(unit: str) -> bool:
    return any(keyword in _norm_text(unit) for keyword in MONEY_UNIT_KEYWORDS)


def _truncate(text: Any, limit: int) -> str:
    normalized = _norm_text(text)
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."


def _customer_readme_df() -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {"topic": "Workbook purpose", "message": "This workbook is a 338A DeepSeek text-only dry-run adjudication plan on top of 337D."},
                {"topic": "Boundaries", "message": "The model only sees compact extracted text evidence. It does not inspect images, does not write back, and does not modify 337D."},
                {"topic": "Safety", "message": "Deterministic guards keep hard constraints above model suggestions. Low-confidence and invalid responses fall back to NEEDS_MORE_CONTEXT."},
            ]
        )
    )


@dataclass
class DeepSeekRuntimeConfig:
    api_key: str
    base_url: str
    model: str
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS


class DeepSeekTextClient:
    def __init__(self, config: DeepSeekRuntimeConfig) -> None:
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
                        "你是一个严格的中文财务文本证据裁决器。"
                        "只能基于提供的文本证据判断，不能使用外部知识，不能输出 markdown，必须只返回 JSON 对象。"
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


def parse_model_json(text: str) -> Tuple[Dict[str, Any] | None, str]:
    cleaned = _norm_text(text)
    if not cleaned:
        return None, "empty_response"
    try:
        return json.loads(cleaned), "raw_json"
    except Exception:
        pass
    if "```" in cleaned:
        parts = cleaned.split("```")
        for part in parts:
            candidate = part.strip()
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


def build_prompt_payload(row: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "instruction": {
            "task": "Judge the row only from provided text evidence.",
            "must_follow": [
                "Do not invent data.",
                "Do not use outside knowledge.",
                "Do not provide investment advice.",
                "Return strict JSON only.",
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
            "document": _norm_text(row.get("document")),
            "source_sheet": _norm_text(row.get("source_sheet")),
            "source_row_no": _safe_int(row.get("source_row_no"), 0),
            "metric": _norm_text(row.get("metric_before")),
            "metric_display_zh": _norm_text(row.get("metric_display_zh")),
            "year": _norm_text(row.get("year_before")),
            "value": _norm_text(row.get("value_before")),
            "unit": _norm_text(row.get("unit_before")),
            "source_page": _norm_text(row.get("source_page")),
            "status_before_adjudication": _norm_text(row.get("status_before")),
            "source_evidence_excerpt": _truncate(row.get("evidence"), MAX_EVIDENCE_LEN),
            "suspicious_reason": _norm_text(row.get("suspicious_reason")),
            "notes": _norm_text(row.get("notes")),
            "route_change_context": _truncate(row.get("route_change_context"), MAX_CONTEXT_LEN),
        },
    }


def build_prompt_text(row: Mapping[str, Any]) -> str:
    payload = build_prompt_payload(row)
    return (
        "请只基于下面的文本证据做严格 JSON 裁决。\n"
        "不要输出 markdown，不要输出解释性前言，不要使用外部知识。\n\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def build_cache_key(row: Mapping[str, Any]) -> str:
    evidence_hash = hashlib.sha256(_norm_text(row.get("evidence")).encode("utf-8")).hexdigest()
    payload = {
        "prompt_version": PROMPT_VERSION,
        "document": _norm_text(row.get("document")),
        "metric": _norm_text(row.get("metric_before")),
        "year": _norm_text(row.get("year_before")),
        "value": _norm_text(row.get("value_before")),
        "unit": _norm_text(row.get("unit_before")),
        "evidence_hash": evidence_hash,
        "suspicious_reason": _norm_text(row.get("suspicious_reason")),
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def prompt_hash(prompt_text: str) -> str:
    return hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()


def validate_evidence_quote(quote: str, evidence: str) -> bool:
    normalized_quote = _norm_text(quote).replace("...", "").replace("…", "")
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
    unit = _norm_text(model_output.get("suggested_unit") or row.get("unit_before"))
    role = _norm_text(model_output.get("table_role_guess"))
    source_sheet = _norm_text(row.get("source_sheet"))
    if role in {"LEGAL_DISCLOSURE_TABLE", "RATING_STANDARD_TABLE"}:
        return "HARD_REJECT_LEGAL_RATING"
    if source_sheet == "02_NEEDS_REVIEW" and _contains_any(_norm_text(row.get("notes")), ["metric_not_allowed_for_reviewed"]):
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


def _contains_any(text: str, patterns: Iterable[str]) -> bool:
    normalized = _norm_text(text).casefold()
    return any(pattern.casefold() in normalized for pattern in patterns)


def _recommended_action(
    model_decision_status: str,
    model_decision: str,
    confidence: float,
    guard_result: str,
) -> Tuple[str, bool]:
    conflict = False
    if model_decision_status == "INVALID_RESPONSE":
        return "NEEDS_MORE_CONTEXT", False
    if guard_result != "PASS":
        if model_decision == "CONFIRM_REVIEWED":
            conflict = True
        if "LEGAL_RATING" in guard_result or "NON_REVIEWABLE_METADATA" in guard_result:
            return "REJECT", conflict
        return "DOWNGRADE_TO_NEEDS_REVIEW", conflict
    if confidence < 0.70:
        return "NEEDS_MORE_CONTEXT", False
    return model_decision or "NEEDS_MORE_CONTEXT", False


def _decision_counts(plan_df: pd.DataFrame, column: str) -> Dict[str, int]:
    if plan_df.empty or column not in plan_df.columns:
        return {}
    values = [_norm_text(value) for value in plan_df[column]]
    counts: Dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


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


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), ensure_ascii=False) + "\n")


def _load_source_rows(workbook_path: Path, limit: int) -> List[Dict[str, Any]]:
    needs_review_df = _read_excel(workbook_path, "02_NEEDS_REVIEW")
    suspicious_df = _read_excel(workbook_path, "08_SUSPICIOUS_REVIEWED_AUDIT")
    route_change_df = _read_excel(workbook_path, "09_ROUTE_CHANGE_TRACE")

    route_context_map: Dict[Tuple[str, str, str, str], str] = {}
    if not route_change_df.empty:
        for record in route_change_df.to_dict(orient="records"):
            key = (
                _norm_text(record.get("document")),
                _norm_text(record.get("metric_after_337d") or record.get("metric_before_337d")),
                _norm_text(record.get("year_after_337d") or record.get("year_before_337d")),
                _norm_text(record.get("source_evidence_excerpt")),
            )
            route_context_map[key] = _truncate(
                " | ".join(
                    filter(
                        None,
                        [
                            _norm_text(record.get("status_before_337d")),
                            _norm_text(record.get("status_after_337d")),
                            _norm_text(record.get("route_reason_before_337d")),
                            _norm_text(record.get("route_reason_after_337d")),
                            _norm_text(record.get("suspicious_reason")),
                            _norm_text(record.get("337d_action")),
                        ],
                    )
                ),
                MAX_CONTEXT_LEN,
            )

    rows: List[Dict[str, Any]] = []
    for index, record in enumerate(suspicious_df.to_dict(orient="records"), start=2):
        route_key = (
            _norm_text(record.get("document")),
            _norm_text(record.get("metric")),
            _norm_text(record.get("year")),
            _norm_text(record.get("evidence")),
        )
        rows.append(
            {
                "source_sheet": "08_SUSPICIOUS_REVIEWED_AUDIT",
                "source_row_no": index,
                "document": _norm_text(record.get("document")),
                "metric_before": _norm_text(record.get("metric")),
                "metric_display_zh": _norm_text(record.get("metric")),
                "year_before": _norm_text(record.get("year")),
                "value_before": _norm_text(record.get("value")),
                "unit_before": _norm_text(record.get("unit")),
                "source_page": _norm_text(record.get("source_page")),
                "status_before": "reviewed_preview",
                "evidence": _truncate(record.get("evidence"), MAX_EVIDENCE_LEN),
                "suspicious_reason": _norm_text(record.get("suspicious_reason")),
                "notes": _norm_text(record.get("337d_action")),
                "route_change_context": route_context_map.get(route_key, ""),
            }
        )
    for index, record in enumerate(needs_review_df.to_dict(orient="records"), start=2):
        rows.append(
            {
                "source_sheet": "02_NEEDS_REVIEW",
                "source_row_no": _safe_int(record.get("row_no"), index),
                "document": _norm_text(record.get("document")),
                "metric_before": _norm_text(record.get("metric")),
                "metric_display_zh": _norm_text(record.get("metric_display_zh")),
                "year_before": _norm_text(record.get("year")),
                "value_before": _norm_text(record.get("value")),
                "unit_before": _norm_text(record.get("unit")),
                "source_page": _norm_text(record.get("source_page")),
                "status_before": _norm_text(record.get("status")),
                "evidence": _truncate(record.get("source_evidence_excerpt"), MAX_EVIDENCE_LEN),
                "suspicious_reason": "",
                "notes": _norm_text(record.get("notes")),
                "route_change_context": "",
            }
        )
    deduped: List[Dict[str, Any]] = []
    seen = set()
    for row in rows:
        dedupe_key = (
            _norm_text(row.get("source_sheet")),
            _norm_text(row.get("document")),
            _norm_text(row.get("metric_before")),
            _norm_text(row.get("year_before")),
            _norm_text(row.get("value_before")),
            _norm_text(row.get("unit_before")),
            _norm_text(row.get("evidence")),
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        deduped.append(row)
        if len(deduped) >= limit:
            break
    for row in deduped:
        row["adjudication_id"] = hashlib.sha256(
            json.dumps(
                {
                    "source_sheet": row["source_sheet"],
                    "source_row_no": row["source_row_no"],
                    "document": row["document"],
                    "metric": row["metric_before"],
                    "year": row["year_before"],
                    "value": row["value_before"],
                },
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()[:16]
    return deduped


def _validate_model_output(parsed: Dict[str, Any] | None, evidence: str) -> Tuple[Dict[str, Any], str, List[str]]:
    errors: List[str] = []
    if parsed is None:
        return {}, "INVALID_RESPONSE", ["json_parse_failed"]
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
    if not validate_evidence_quote(evidence_quote, evidence):
        errors.append("evidence_quote_not_grounded")
    status = "VALID" if not errors else "INVALID_RESPONSE"
    return parsed, status, errors


def build_deepseek_text_adjudicator_338a(
    *,
    reviewed_strictness_337d_dir: Path,
    output_dir: Path,
    limit: int = DEFAULT_LIMIT,
    dry_run_prompts_only: bool = False,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    client: DeepSeekTextClient | None = None,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_status_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)

    workbook_path = reviewed_strictness_337d_dir / "real_test_mineru_client_export_337d.xlsx"
    before_after_path = reviewed_strictness_337d_dir / "reviewed_strictness_year_alignment_337d_before_after.xlsx"
    summary_337d_path = reviewed_strictness_337d_dir / "reviewed_strictness_year_alignment_337d_summary.json"
    blocked_reasons: List[str] = []
    for path in [workbook_path, before_after_path, summary_337d_path]:
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
            "qa_json": {"decision": BLOCKED_DECISION, "qa_fail_count": len(blocked_reasons), "checks": [], "blocked_reasons": blocked_reasons},
            "workbook_sheets": {},
            "prompt_preview_rows": [],
            "cache_rows": [],
        }

    summary_337d = json.loads(summary_337d_path.read_text(encoding="utf-8"))
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "")
    model_name = os.environ.get("DEEPSEEK_MODEL", "")
    api_env_ready = bool(_norm_text(api_key) and _norm_text(base_url) and _norm_text(model_name))

    source_rows = _load_source_rows(workbook_path, limit=max(1, int(limit)))
    cache_path = output_dir / "deepseek_text_adjudication_cache_338a.jsonl"
    cache_map = _load_cache(cache_path)

    prompt_preview_rows: List[Dict[str, Any]] = []
    cache_rows: Dict[str, Dict[str, Any]] = dict(cache_map)
    plan_rows: List[Dict[str, Any]] = []
    invalid_or_low_confidence_rows: List[Dict[str, Any]] = []
    conflict_rows: List[Dict[str, Any]] = []

    if client is None and api_env_ready and not dry_run_prompts_only:
        client = DeepSeekTextClient(
            DeepSeekRuntimeConfig(
                api_key=api_key,
                base_url=base_url,
                model=model_name,
                timeout_seconds=timeout_seconds,
            )
        )

    total_calls = 0
    cache_hit_count = 0
    invalid_response_count = 0
    low_confidence_count = 0
    rule_model_conflict_count = 0

    for row in source_rows:
        prompt_text = build_prompt_text(row)
        cache_key = build_cache_key(row)
        prompt_sha = prompt_hash(prompt_text)
        prompt_preview_rows.append(
            {
                "adjudication_id": row["adjudication_id"],
                "document": row["document"],
                "source_sheet": row["source_sheet"],
                "source_row_no": row["source_row_no"],
                "metric_before": row["metric_before"],
                "year_before": row["year_before"],
                "value_before": row["value_before"],
                "unit_before": row["unit_before"],
                "prompt_hash": prompt_sha,
                "prompt_text": prompt_text,
            }
        )

        raw_content = ""
        raw_response_obj: Dict[str, Any] = {}
        parse_method = "not_run"
        cache_hit = False
        if cache_key in cache_rows:
            cache_entry = cache_rows[cache_key]
            raw_content = _norm_text(cache_entry.get("raw_content"))
            raw_response_obj = cache_entry.get("parsed_response") or {}
            parse_method = _norm_text(cache_entry.get("parse_method")) or "cache"
            cache_hit = True
            cache_hit_count += 1
        elif not dry_run_prompts_only and api_env_ready and client is not None:
            total_calls += 1
            try:
                call_result = client.adjudicate(prompt_text)
                raw_content = _norm_text(call_result.get("content"))
                raw_response_obj = call_result.get("raw_response") or {}
            except Exception as exc:
                raw_content = json.dumps(
                    {
                        "decision": "NEEDS_MORE_CONTEXT",
                        "suggested_metric": None,
                        "suggested_year": None,
                        "suggested_value": None,
                        "suggested_unit": None,
                        "table_role_guess": "UNKNOWN",
                        "risk_flags": ["api_error"],
                        "confidence": 0.0,
                        "reason": f"API 调用失败: {_truncate(str(exc), 120)}",
                        "evidence_quote": _truncate(row["evidence"], 40),
                    },
                    ensure_ascii=False,
                )
                raw_response_obj = {"error": str(exc)}
            parsed_response, parse_method = parse_model_json(raw_content)
            cache_rows[cache_key] = {
                "cache_key": cache_key,
                "prompt_hash": prompt_sha,
                "model_name": model_name,
                "raw_content": raw_content,
                "parsed_response": parsed_response,
                "parse_method": parse_method,
                "cached_at_utc": _utc_now(),
            }
        else:
            parsed_response = None
            parse_method = "prompts_only"
            raw_content = ""

        if cache_hit:
            parsed_response = cache_rows[cache_key].get("parsed_response")
        elif dry_run_prompts_only or not api_env_ready:
            parsed_response = None

        parsed_response, model_decision_status, validation_errors = _validate_model_output(parsed_response, row["evidence"])
        model_decision = _norm_text(parsed_response.get("decision")) if parsed_response else ""
        confidence_value = 0.0
        try:
            confidence_value = float(parsed_response.get("confidence", 0.0)) if parsed_response else 0.0
        except Exception:
            confidence_value = 0.0

        guard_result = deterministic_guard(row, parsed_response or {})
        recommended_final_action, conflict = _recommended_action(
            model_decision_status=model_decision_status,
            model_decision=model_decision,
            confidence=confidence_value,
            guard_result=guard_result,
        )

        if model_decision_status == "INVALID_RESPONSE":
            invalid_response_count += 1
        elif confidence_value < 0.70:
            low_confidence_count += 1
        if conflict:
            rule_model_conflict_count += 1

        plan_row = {
            "adjudication_id": row["adjudication_id"],
            "document": row["document"],
            "source_sheet": row["source_sheet"],
            "source_row_no": row["source_row_no"],
            "metric_before": row["metric_before"],
            "metric_display_zh": row["metric_display_zh"],
            "year_before": row["year_before"],
            "value_before": row["value_before"],
            "unit_before": row["unit_before"],
            "source_page": row["source_page"],
            "status_before": row["status_before"],
            "evidence": row["evidence"],
            "suspicious_reason": row["suspicious_reason"],
            "notes": row["notes"],
            "route_change_context": row["route_change_context"],
            "model_decision_status": model_decision_status if not dry_run_prompts_only and api_env_ready else ("NOT_RUN" if dry_run_prompts_only else "BLOCKED_MISSING_DEEPSEEK_API_KEY"),
            "model_decision": model_decision or ("NEEDS_MORE_CONTEXT" if model_decision_status == "INVALID_RESPONSE" else ""),
            "suggested_metric": _norm_text(parsed_response.get("suggested_metric")) if parsed_response else "",
            "suggested_year": _norm_text(parsed_response.get("suggested_year")) if parsed_response else "",
            "suggested_value": _norm_text(parsed_response.get("suggested_value")) if parsed_response else "",
            "suggested_unit": _norm_text(parsed_response.get("suggested_unit")) if parsed_response else "",
            "table_role_guess": _norm_text(parsed_response.get("table_role_guess")) if parsed_response else "",
            "confidence": confidence_value,
            "risk_flags": "|".join(parsed_response.get("risk_flags", [])) if parsed_response and isinstance(parsed_response.get("risk_flags"), list) else "",
            "reason": _norm_text(parsed_response.get("reason")) if parsed_response else "",
            "evidence_quote": _norm_text(parsed_response.get("evidence_quote")) if parsed_response else "",
            "deterministic_guard_result": guard_result,
            "recommended_final_action": recommended_final_action if (parsed_response or not api_env_ready or dry_run_prompts_only) else "NEEDS_MORE_CONTEXT",
            "model_name": model_name,
            "prompt_hash": prompt_sha,
            "cache_hit": cache_hit,
            "parse_method": parse_method,
            "validation_errors": "|".join(validation_errors),
        }
        plan_rows.append(plan_row)
        if model_decision_status == "INVALID_RESPONSE" or confidence_value < 0.70:
            invalid_or_low_confidence_rows.append(plan_row)
        if conflict or guard_result != "PASS" and model_decision == "CONFIRM_REVIEWED":
            conflict_rows.append(plan_row)

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_status_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)
    protected_cached_after = _git_cached_names_for_paths(PROTECTED_DIRTY_PATHS)

    plan_df = _clean_frame(pd.DataFrame(plan_rows))
    summary_counts = _decision_counts(plan_df, "recommended_final_action")
    model_counts = _decision_counts(plan_df, "model_decision")

    if dry_run_prompts_only:
        decision = PROMPTS_ONLY_DECISION
    elif not api_env_ready:
        decision = BLOCKED_MISSING_KEY_DECISION
    else:
        decision = READY_DECISION

    qa_checks = [
        {"check_name": "input_337d_workbook_exists", "status": "PASS" if workbook_path.exists() else "FAIL", "detail": str(workbook_path)},
        {"check_name": "prompt_preview_generated", "status": "PASS" if len(prompt_preview_rows) == len(source_rows) else "FAIL", "detail": f"{len(prompt_preview_rows)} / {len(source_rows)}"},
        {"check_name": "plan_row_count_matches_limit", "status": "PASS" if len(plan_rows) == len(source_rows) else "FAIL", "detail": f"{len(plan_rows)} / {len(source_rows)}"},
        {"check_name": "official_assets_unchanged", "status": "PASS" if official_assets_before == official_assets_after else "FAIL", "detail": json.dumps(official_assets_after, ensure_ascii=False)},
        {"check_name": "protected_dirty_status_preserved", "status": "PASS" if protected_status_before == protected_status_after else "FAIL", "detail": json.dumps(protected_status_after, ensure_ascii=False)},
        {"check_name": "protected_dirty_paths_not_staged", "status": "PASS" if not protected_cached_after else "FAIL", "detail": json.dumps(protected_cached_after, ensure_ascii=False)},
    ]
    if not dry_run_prompts_only and api_env_ready:
        qa_checks.append(
            {
                "check_name": "cache_or_api_result_present",
                "status": "PASS" if len(plan_rows) > 0 else "FAIL",
                "detail": str(len(plan_rows)),
            }
        )

    qa_fail_count = sum(1 for check in qa_checks if check["status"] == "FAIL")
    if qa_fail_count and decision == READY_DECISION:
        decision = PARTIAL_DECISION

    summary = {
        "generated_at_utc": _utc_now(),
        "client_ready": False,
        "production_ready": False,
        "reviewed_strictness_337d_dir": str(reviewed_strictness_337d_dir),
        "output_dir": str(output_dir),
        "api_env_ready": api_env_ready,
        "dry_run_prompts_only": dry_run_prompts_only,
        "model_name": model_name,
        "adjudication_row_count": len(plan_rows),
        "api_call_count": total_calls,
        "cache_hit_count": cache_hit_count,
        "confirm_reviewed_count": summary_counts.get("CONFIRM_REVIEWED", 0),
        "downgrade_to_needs_review_count": summary_counts.get("DOWNGRADE_TO_NEEDS_REVIEW", 0),
        "reject_count": summary_counts.get("REJECT", 0),
        "needs_more_context_count": summary_counts.get("NEEDS_MORE_CONTEXT", 0),
        "model_confirm_reviewed_count": model_counts.get("CONFIRM_REVIEWED", 0),
        "model_downgrade_count": model_counts.get("DOWNGRADE_TO_NEEDS_REVIEW", 0),
        "model_reject_count": model_counts.get("REJECT", 0),
        "model_needs_more_context_count": model_counts.get("NEEDS_MORE_CONTEXT", 0),
        "invalid_response_count": invalid_response_count,
        "low_confidence_count": low_confidence_count,
        "rule_model_conflict_count": rule_model_conflict_count,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
    }

    manifest = {
        "task": "338A_deepseek_text_adjudicator_dry_run",
        "reviewed_strictness_337d_dir": str(reviewed_strictness_337d_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / "deepseek_text_adjudicator_338a_summary.json"),
            "manifest_json": str(output_dir / "deepseek_text_adjudicator_338a_manifest.json"),
            "qa_json": str(output_dir / "deepseek_text_adjudicator_338a_qa.json"),
            "report_md": str(output_dir / "deepseek_text_adjudicator_338a_report.md"),
            "plan_xlsx": str(output_dir / "deepseek_text_adjudication_plan_338a.xlsx"),
            "cache_jsonl": str(output_dir / "deepseek_text_adjudication_cache_338a.jsonl"),
            "prompt_preview_jsonl": str(output_dir / "deepseek_text_adjudication_prompts_preview_338a.jsonl"),
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

    summary_sheet_df = _clean_frame(pd.DataFrame([summary]))
    cost_cache_summary_df = _clean_frame(
        pd.DataFrame(
            [
                {
                    "model_name": model_name,
                    "api_env_ready": api_env_ready,
                    "dry_run_prompts_only": dry_run_prompts_only,
                    "adjudication_row_count": len(plan_rows),
                    "api_call_count": total_calls,
                    "cache_hit_count": cache_hit_count,
                    "cache_write_count": max(len(cache_rows) - len(cache_map), 0),
                }
            ]
        )
    )

    workbook_sheets = {
        "00_README": _customer_readme_df(),
        "01_ADJUDICATION_SUMMARY": summary_sheet_df,
        "02_MODEL_ADJUDICATION_PLAN": plan_df,
        "03_PROMPT_PREVIEW": _clean_frame(pd.DataFrame(prompt_preview_rows)),
        "04_INVALID_OR_LOW_CONFIDENCE": _clean_frame(pd.DataFrame(invalid_or_low_confidence_rows)),
        "05_RULE_MODEL_CONFLICTS": _clean_frame(pd.DataFrame(conflict_rows)),
        "06_COST_AND_CACHE_SUMMARY": cost_cache_summary_df,
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "workbook_sheets": workbook_sheets,
        "prompt_preview_rows": prompt_preview_rows,
        "cache_rows": list(cache_rows.values()),
    }
