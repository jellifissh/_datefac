import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

BASE_DIR = Path(r"D:\_datefac")
IN_7M_SUMMARY = BASE_DIR / "output" / "stage7m_three_case_strict_schema_api_dry_run" / "194_stage7m_three_case_summary.json"
IN_7M_SELECTED = BASE_DIR / "output" / "stage7m_three_case_strict_schema_api_dry_run" / "194_stage7m_selected_requests.jsonl"
IN_7M_RAW = BASE_DIR / "output" / "stage7m_three_case_strict_schema_api_dry_run" / "194_stage7m_raw_responses_sanitized.jsonl"
IN_7M_AUDIT = BASE_DIR / "output" / "stage7m_three_case_strict_schema_api_dry_run" / "194_stage7m_validation_audit.xlsx"
IN_7I_REQUESTS = BASE_DIR / "output" / "stage7i_ai_runtime_dry_run" / "188_stage7i_ai_review_requests.jsonl"
IN_7G_REMAINING = BASE_DIR / "output" / "stage7g_manual_review_reduction_sandbox" / "186_stage7g_remaining_manual_review.xlsx"
IN_SCHEMA = BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_ai_review_response_schema.json"
IN_RULES = BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_ai_validation_rules.json"

OUT_DIR = BASE_DIR / "output" / "stage7m_fix_request_slimming"
OUT_SUMMARY = OUT_DIR / "195_stage7m_fix_request_slimming_summary.json"
OUT_REPORT = OUT_DIR / "195_stage7m_fix_request_slimming_report.md"
OUT_AUDIT = OUT_DIR / "195_stage7m_request_size_audit.xlsx"
OUT_SLIM = OUT_DIR / "195_stage7m_slim_selected_requests.jsonl"
OUT_PLAN = OUT_DIR / "195_stage7m2_retry_plan.md"

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

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
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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


def _build_original_prompt(req: Dict[str, Any], schema: Dict[str, Any]) -> str:
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


def _build_slim_prompt(req: Dict[str, Any], schema: Dict[str, Any]) -> str:
    slim_rows = []
    for row in req.get("candidate_rows", []):
        slim_rows.append(
            {
                "row_id": _norm(row.get("row_id")),
                "statement_type": _norm(row.get("statement_type")),
                "normalized_metric_name": _norm(row.get("normalized_metric_name")),
                "raw_metric_name": _norm(row.get("raw_metric_name")),
                "year": _norm(row.get("year")),
                "value": _norm(row.get("value")),
                "unit": _norm(row.get("unit")),
                "source_page": _norm(row.get("source_page")),
                "source_text_excerpt": _norm(row.get("source_text_excerpt"))[:120],
            }
        )
    required_fields = schema.get("required", [])
    template = {
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
        "manual_review_reason": _norm(req.get("manual_review_reason")),
        "candidate_rows": slim_rows,
    }
    return (
        "仅返回一个 JSON object，不要解释。\n"
        "必须包含字段：" + ", ".join(required_fields) + "。\n"
        "规则：row_id/value 不得编造；EPS 不得 ratio；requires_human_approval=true。\n"
        "参考模板：" + json.dumps(template, ensure_ascii=False) + "\n"
        "输入：" + json.dumps(payload, ensure_ascii=False)
    )


def _slim_request(req: Dict[str, Any]) -> Dict[str, Any]:
    out = {
        "review_id": _norm(req.get("review_id")),
        "source_pdf": _norm(req.get("source_pdf")),
        "conflict_group_id": _norm(req.get("conflict_group_id")),
        "manual_review_reason": _norm(req.get("manual_review_reason")),
        "candidate_rows": [],
        "known_rules": {"eps_unit": "元/股", "do_not_use_ratio_for_eps": True},
    }
    for row in req.get("candidate_rows", []):
        out["candidate_rows"].append(
            {
                "row_id": _norm(row.get("row_id")),
                "statement_type": _norm(row.get("statement_type")),
                "normalized_metric_name": _norm(row.get("normalized_metric_name")),
                "raw_metric_name": _norm(row.get("raw_metric_name")),
                "year": _norm(row.get("year")),
                "value": _norm(row.get("value")),
                "unit": _norm(row.get("unit")),
                "source_page": _norm(row.get("source_page")),
                "source_text_excerpt": _norm(row.get("source_text_excerpt"))[:120],
            }
        )
    return out


def _is_eps(req: Dict[str, Any]) -> bool:
    for row in req.get("candidate_rows", []):
        text = (_norm(row.get("normalized_metric_name")) + " " + _norm(row.get("raw_metric_name"))).lower()
        if "eps" in text or "每股收益" in text:
            return True
    return False


def _metric_name(req: Dict[str, Any]) -> str:
    if req.get("candidate_rows"):
        row = req["candidate_rows"][0]
        return _norm(row.get("normalized_metric_name")) or _norm(row.get("raw_metric_name"))
    return ""


def _pick_slim_three(pool: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    lightweight = [r for r in pool if len(r.get("candidate_rows", [])) <= 5]
    if not lightweight:
        lightweight = pool[:]

    # Prefer one amount-like, one ratio-like, one valuation-like (if available)
    def category(req: Dict[str, Any]) -> str:
        m = _metric_name(req).lower()
        if any(x in m for x in ["p/e", "p/b", "pe", "pb", "ev/ebitda", "毛利率", "roe", "ratio", "率"]):
            return "ratio_or_valuation"
        if any(x in m for x in ["营业收入", "净利润", "利润", "收入"]):
            return "amount_like"
        return "other"

    picks: List[Dict[str, Any]] = []
    used = set()
    used_metrics = set()
    # amount-like first
    amount = sorted([r for r in lightweight if category(r) == "amount_like"], key=lambda x: (len(x.get("candidate_rows", [])), _norm(x.get("review_id"))))
    ratio = sorted([r for r in lightweight if category(r) == "ratio_or_valuation"], key=lambda x: (len(x.get("candidate_rows", [])), _norm(x.get("review_id"))))
    other = sorted([r for r in lightweight if category(r) == "other"], key=lambda x: (len(x.get("candidate_rows", [])), _norm(x.get("review_id"))))

    for bucket in [amount, ratio, other, ratio]:
        for r in bucket:
            rid = _norm(r.get("review_id"))
            if rid in used:
                continue
            metric = _metric_name(r)
            if metric and metric in used_metrics:
                continue
            picks.append(r)
            used.add(rid)
            if metric:
                used_metrics.add(metric)
            break
        if len(picks) >= 3:
            break

    if len(picks) < 3:
        for r in sorted(lightweight, key=lambda x: (len(x.get("candidate_rows", [])), _norm(x.get("review_id")))):
            rid = _norm(r.get("review_id"))
            if rid in used:
                continue
            metric = _metric_name(r)
            # prefer metric diversity when available
            if metric and metric in used_metrics:
                continue
            picks.append(r)
            used.add(rid)
            if metric:
                used_metrics.add(metric)
            if len(picks) >= 3:
                break
        # hard fill without metric constraint if still short
        if len(picks) < 3:
            for r in sorted(lightweight, key=lambda x: (len(x.get("candidate_rows", [])), _norm(x.get("review_id")))):
                rid = _norm(r.get("review_id"))
                if rid in used:
                    continue
                picks.append(r)
                used.add(rid)
                if len(picks) >= 3:
                    break
    picks = picks[:3]

    meta = {
        "lightweight_pool_count": len(lightweight),
        "lightweight_threshold_candidate_rows": 5,
        "selected_metrics": [_metric_name(x) for x in picks],
        "selected_candidate_rows": [len(x.get("candidate_rows", [])) for x in picks],
    }
    return picks, meta


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    required = [IN_7M_SUMMARY, IN_7M_SELECTED, IN_7M_RAW, IN_7M_AUDIT, IN_7I_REQUESTS, IN_7G_REMAINING, IN_SCHEMA, IN_RULES]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "stage7m_fix_request_slimming",
                "mode": "analysis_only_no_api_call",
                "external_api_called": False,
                "blocked": True,
                "blocked_reason": "|".join(missing),
            },
        )
        return 0

    before = _snapshot_hashes()

    s7m_summary = _load_json(IN_7M_SUMMARY)
    s7m_selected = _load_jsonl(IN_7M_SELECTED)
    s7m_raw = _load_jsonl(IN_7M_RAW)
    _ = pd.read_excel(IN_7M_AUDIT)
    pool_requests = _load_jsonl(IN_7I_REQUESTS)
    remaining_df = pd.read_excel(IN_7G_REMAINING)
    schema = _load_json(IN_SCHEMA)
    _rules = _load_json(IN_RULES)

    timeout_rows = [r for r in s7m_raw if bool(r.get("timeout")) or "timeout" in _norm(r.get("error")).lower()]
    timeout_request_ids = [_norm(r.get("review_id")) for r in timeout_rows]
    timeout_request_identified = len(timeout_rows) > 0

    audit_rows: List[Dict[str, Any]] = []
    for req in s7m_selected:
        rid = _norm(req.get("review_id"))
        candidate_rows = req.get("candidate_rows", [])
        candidate_count = len(candidate_rows)
        excerpt_lengths = [len(_norm(c.get("source_text_excerpt"))) for c in candidate_rows]
        source_excerpt_total_len = int(sum(excerpt_lengths))
        source_excerpt_max_len = int(max(excerpt_lengths) if excerpt_lengths else 0)
        row_field_counts = [len(c.keys()) for c in candidate_rows]
        avg_field_count = float(sum(row_field_counts) / len(row_field_counts)) if row_field_counts else 0.0
        contains_long_text = bool(source_excerpt_max_len > 180)
        contains_pipe_dense_text = any(_norm(c.get("source_text_excerpt")).count("|") >= 6 for c in candidate_rows)

        original_prompt_chars = len(_build_original_prompt(req, schema))
        slim_prompt_chars_same_req = len(_build_slim_prompt(_slim_request(req), schema))
        reduction_rate_same_req = (original_prompt_chars - slim_prompt_chars_same_req) / original_prompt_chars if original_prompt_chars else 0.0

        timed_out = rid in timeout_request_ids
        likely_timeout_risk = candidate_count >= 5 or original_prompt_chars >= 3500 or source_excerpt_total_len >= 250

        audit_rows.append(
            {
                "review_id": rid,
                "manual_review_reason": _norm(req.get("manual_review_reason")),
                "normalized_metric_name": _metric_name(req),
                "candidate_rows_count": candidate_count,
                "prompt_chars_estimated_original": original_prompt_chars,
                "prompt_chars_estimated_slim_same_request": slim_prompt_chars_same_req,
                "prompt_reduction_rate_same_request": round(reduction_rate_same_req, 6),
                "source_text_excerpt_total_len": source_excerpt_total_len,
                "source_text_excerpt_max_len": source_excerpt_max_len,
                "avg_candidate_row_field_count": round(avg_field_count, 2),
                "contains_long_text_excerpt": contains_long_text,
                "contains_pipe_dense_text": contains_pipe_dense_text,
                "timed_out_in_stage7m": timed_out,
                "likely_timeout_risk": likely_timeout_risk,
            }
        )

    pd.DataFrame(audit_rows).to_excel(OUT_AUDIT, index=False)

    # timeout probable reason
    timeout_probable_reason = "service_latency_or_network_jitter"
    if timeout_request_identified:
        t_id = timeout_request_ids[0]
        t_row = next((r for r in audit_rows if r["review_id"] == t_id), None)
        if t_row and (t_row["candidate_rows_count"] >= 5 and t_row["source_text_excerpt_total_len"] >= 250):
            timeout_probable_reason = "high_candidate_row_count_plus_long_prompt_context"
        elif t_row and t_row["prompt_chars_estimated_original"] >= max(x["prompt_chars_estimated_original"] for x in audit_rows):
            timeout_probable_reason = "largest_prompt_in_batch_plus_service_latency"
        else:
            timeout_probable_reason = "service_latency_or_network_jitter"

    # pool category availability checks
    stage7i_reasons = sorted({_norm(r.get("manual_review_reason")) for r in pool_requests})
    remaining_reasons = sorted({_norm(x) for x in remaining_df.get("manual_review_reason", pd.Series(dtype=str)).dropna().tolist()})
    remaining_conflict_categories = sorted({_norm(x) for x in remaining_df.get("conflict_category", pd.Series(dtype=str)).dropna().tolist()})

    required_categories = ["true_value_conflict", "unit_semantics_uncertain", "amount_vs_ratio_collision"]
    available_in_request_pool = set(stage7i_reasons) | set(remaining_reasons)
    # Also count conflict_category as evidence source
    available_with_conflict_category = available_in_request_pool | set(remaining_conflict_categories)
    missing_categories = [c for c in required_categories if c not in available_with_conflict_category]

    eps_case_available = any(_is_eps(r) for r in pool_requests)

    # slim selection
    slim_selected_raw, selection_meta = _pick_slim_three(pool_requests)
    slim_selected = [_slim_request(r) for r in slim_selected_raw]
    _write_jsonl(OUT_SLIM, slim_selected)

    original_max_prompt_chars = max((r["prompt_chars_estimated_original"] for r in audit_rows), default=0)
    slim_max_prompt_chars = max((len(_build_slim_prompt(r, schema)) for r in slim_selected), default=0)
    prompt_reduction_rate = ((original_max_prompt_chars - slim_max_prompt_chars) / original_max_prompt_chars) if original_max_prompt_chars else 0.0

    after = _snapshot_hashes()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]
    delivery = _run_delivery_check()
    check_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "stage7m_fix_request_slimming",
        "mode": "analysis_only_no_api_call",
        "based_on_stage7m_commit": "363a43832dd79bc92930bb6e159837d232b7c569",
        "external_api_called": False,
        "stage7m_selected_request_count": int(s7m_summary.get("selected_review_request_count", 0)),
        "stage7m_timeout_count": int(s7m_summary.get("timeout_count", 0)),
        "timeout_request_identified": timeout_request_identified,
        "timeout_probable_reason": timeout_probable_reason,
        "timeout_request_ids": timeout_request_ids,
        "original_max_prompt_chars": int(original_max_prompt_chars),
        "slim_max_prompt_chars": int(slim_max_prompt_chars),
        "prompt_reduction_rate": round(prompt_reduction_rate, 6),
        "slim_selected_request_count": len(slim_selected),
        "eps_case_available": eps_case_available,
        "request_pool_missing_categories": missing_categories,
        "stage7i_manual_review_reason_set": stage7i_reasons,
        "stage7g_manual_review_reason_set": remaining_reasons,
        "stage7g_conflict_category_set": remaining_conflict_categories,
        "stage7m2_recommended": True,
        "recommended_timeout_seconds": 120,
        "recommended_max_tokens": 700,
        "recommended_request_interval_seconds": 15,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": check_status,
        "selection_meta": selection_meta,
    }
    _write_json(OUT_SUMMARY, summary)

    report = f"""# Stage7M-Fix Request Slimming

## Scope
- external_api_called: false
- stage7m_selected_request_count: {summary['stage7m_selected_request_count']}
- stage7m_timeout_count: {summary['stage7m_timeout_count']}

## Timeout Diagnosis
- timeout_request_identified: {summary['timeout_request_identified']}
- timeout_request_ids: {summary['timeout_request_ids']}
- timeout_probable_reason: {summary['timeout_probable_reason']}

## Prompt Size
- original_max_prompt_chars: {summary['original_max_prompt_chars']}
- slim_max_prompt_chars: {summary['slim_max_prompt_chars']}
- prompt_reduction_rate: {summary['prompt_reduction_rate']}

## Request Pool Coverage
- eps_case_available: {summary['eps_case_available']}
- request_pool_missing_categories: {summary['request_pool_missing_categories']}
- stage7i_manual_review_reason_set: {summary['stage7i_manual_review_reason_set']}
- stage7g_conflict_category_set: {summary['stage7g_conflict_category_set']}

## Stage7M2 Recommendation
- stage7m2_recommended: {summary['stage7m2_recommended']}
- recommended_timeout_seconds: {summary['recommended_timeout_seconds']}
- recommended_max_tokens: {summary['recommended_max_tokens']}
- recommended_request_interval_seconds: {summary['recommended_request_interval_seconds']}

## Safety
- production_files_modified: {summary['production_files_modified']}
- official_02b_modified: {summary['official_02b_modified']}
- formal_rules_modified: {summary['formal_rules_modified']}
- standardizer_modified: {summary['standardizer_modified']}
- release_package_modified: {summary['release_package_modified']}
- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}
"""
    _write_md(OUT_REPORT, report)

    plan = """# Stage7M2 Retry Plan (Slim Requests, No Real Apply)

1. Use `195_stage7m_slim_selected_requests.jsonl` as the only request input.
2. Keep strict schema output requirement unchanged from Stage7K2.
3. Runtime settings:
- timeout_seconds=120
- max_tokens=700
- temperature=0
- inter_request_interval_seconds=15
- non-concurrent, one request at a time
- no automatic retries; stop expansion on first timeout/429
4. Validation gates:
- schema required fields all present
- suggested_row_ids subset of candidate row ids
- suggested_value must come from candidate row values
- EPS must not be ratio
- requires_human_approval must be true
5. Safety gates:
- sandbox only, no real apply
- do not write production 06
- do not change formal rules/official overrides/standardizer/release package
"""
    _write_md(OUT_PLAN, plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
