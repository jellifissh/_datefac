import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

BASE_DIR = Path(r"D:\_datefac")
IN_DIR = BASE_DIR / "output" / "stage7g_manual_review_reduction_sandbox"
STAGE7D_DIR = BASE_DIR / "output" / "stage7d_pipeline_sandbox"
OUT_DIR = BASE_DIR / "output" / "stage7h_ai_assisted_review_design"

IN_SUMMARY = IN_DIR / "186_stage7g_manual_review_reduction_summary.json"
IN_REMAIN = IN_DIR / "186_stage7g_remaining_manual_review.xlsx"
IN_CLASSIFIED = IN_DIR / "186_stage7g_manual_review_classified.xlsx"
IN_POLICY_SUGGEST = IN_DIR / "186_stage7g_updated_policy_suggestions.json"
IN_REDUCED_PREVIEW = IN_DIR / "186_stage7g_reduced_clean_06_preview.xlsx"
IN_STAGE7D_CLASSIFIED = STAGE7D_DIR / "183_stage7d_classified_structured_table.xlsx"

OUT_SUMMARY = OUT_DIR / "187_stage7h_ai_review_design_summary.json"
OUT_REPORT = OUT_DIR / "187_stage7h_ai_review_design_report.md"
OUT_REQ_SCHEMA = OUT_DIR / "187_stage7h_ai_review_request_schema.json"
OUT_RESP_SCHEMA = OUT_DIR / "187_stage7h_ai_review_response_schema.json"
OUT_PROMPT = OUT_DIR / "187_stage7h_prompt_template.md"
OUT_MOCK_REQ = OUT_DIR / "187_stage7h_mock_review_requests.jsonl"
OUT_MOCK_RESP = OUT_DIR / "187_stage7h_mock_review_responses.jsonl"
OUT_VALIDATION = OUT_DIR / "187_stage7h_ai_validation_rules.json"
OUT_RUNTIME_PLAN = OUT_DIR / "187_stage7h_runtime_integration_plan.md"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

EPS_ALIASES = {"EPS", "每股收益"}
ALLOWED_ACTIONS = {"accept_one", "merge_same_value", "split_metric", "exclude", "keep_manual_review"}


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _to_float(v: Any) -> float:
    s = _norm(v).replace(",", "")
    try:
        return float(s)
    except Exception:
        return float("nan")


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


def _load_inputs() -> Tuple[Dict[str, Any], pd.DataFrame, pd.DataFrame, Dict[str, Any], pd.DataFrame, pd.DataFrame]:
    s = json.loads(IN_SUMMARY.read_text(encoding="utf-8"))
    remain = pd.read_excel(IN_REMAIN, sheet_name="remaining_manual_review").fillna("")
    classified = pd.read_excel(IN_CLASSIFIED, sheet_name="manual_review_classified").fillna("")
    pol = json.loads(IN_POLICY_SUGGEST.read_text(encoding="utf-8"))
    reduced = pd.read_excel(IN_REDUCED_PREVIEW, sheet_name="reduced_clean_06_preview").fillna("")
    s7d_cls = pd.read_excel(IN_STAGE7D_CLASSIFIED).fillna("")
    return s, remain, classified, pol, reduced, s7d_cls


def _build_request_schema() -> Dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Stage7HAIReviewRequest",
        "type": "object",
        "required": [
            "review_id",
            "source_pdf",
            "conflict_group_id",
            "manual_review_reason",
            "candidate_rows",
            "current_policy_context",
            "known_rules",
        ],
        "properties": {
            "review_id": {"type": "string"},
            "source_pdf": {"type": "string"},
            "conflict_group_id": {"type": "string"},
            "manual_review_reason": {"type": "string"},
            "candidate_rows": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": [
                        "row_id",
                        "statement_type",
                        "raw_metric_name",
                        "normalized_metric_name",
                        "year",
                        "value",
                        "unit",
                        "source_page",
                        "source_table_id",
                        "source_text_excerpt",
                        "extraction_confidence",
                        "unit_confidence",
                        "classification_confidence",
                    ],
                    "properties": {
                        "row_id": {"type": "string"},
                        "statement_type": {"type": "string"},
                        "raw_metric_name": {"type": "string"},
                        "normalized_metric_name": {"type": "string"},
                        "year": {"type": "string"},
                        "value": {"type": "string"},
                        "unit": {"type": "string"},
                        "source_page": {"type": "string"},
                        "source_table_id": {"type": "string"},
                        "source_text_excerpt": {"type": "string"},
                        "extraction_confidence": {"type": "string"},
                        "unit_confidence": {"type": "string"},
                        "classification_confidence": {"type": "string"},
                    },
                },
            },
            "current_policy_context": {"type": "object"},
            "known_rules": {
                "type": "object",
                "required": ["eps_unit", "do_not_use_ratio_for_eps"],
                "properties": {
                    "eps_unit": {"type": "string", "const": "元/股"},
                    "do_not_use_ratio_for_eps": {"type": "boolean", "const": True},
                },
            },
        },
    }


def _build_response_schema() -> Dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Stage7HAIReviewResponse",
        "type": "object",
        "required": [
            "review_id",
            "suggested_action",
            "suggested_row_ids",
            "suggested_metric_name",
            "suggested_year",
            "suggested_value",
            "suggested_unit",
            "confidence",
            "reasoning_summary",
            "risk_flags",
            "requires_human_approval",
        ],
        "properties": {
            "review_id": {"type": "string"},
            "suggested_action": {
                "type": "string",
                "enum": ["accept_one", "merge_same_value", "split_metric", "exclude", "keep_manual_review"],
            },
            "suggested_row_ids": {"type": "array", "items": {"type": "string"}},
            "suggested_metric_name": {"type": "string"},
            "suggested_year": {"type": "string"},
            "suggested_value": {"type": "string"},
            "suggested_unit": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "reasoning_summary": {"type": "string"},
            "risk_flags": {"type": "array", "items": {"type": "string"}},
            "requires_human_approval": {"type": "boolean"},
        },
    }


def _build_prompt_template() -> str:
    return """# Stage7H AI-Assisted Manual Review Prompt Template

You are an assistant for sandbox-only financial metric conflict review.

## Hard constraints
1. Do NOT call external tools or APIs.
2. Do NOT write or modify production files.
3. Do NOT modify formal rules.
4. Do NOT produce values that are not present in candidate_rows.
5. For EPS/每股收益, do NOT suggest ratio/% as final unit.
6. If evidence is insufficient, return keep_manual_review.

## Input
You will receive one JSON object that follows `187_stage7h_ai_review_request_schema.json`.

## Task
Return exactly one JSON object following `187_stage7h_ai_review_response_schema.json`.

## Decision guideline
- Prefer `accept_one` only when one candidate has clearly stronger evidence.
- Use `merge_same_value` only when candidate values are effectively same and traceable.
- Use `split_metric` when same name actually contains different semantics.
- Use `exclude` when candidate is clearly non-core/noise.
- Use `keep_manual_review` when ambiguity remains.

## Output requirement
- Output JSON only.
- Keep reasoning_summary concise and evidence-based.
- Set `requires_human_approval=true` for all true_value_conflict-like cases.
"""


def _build_validation_rules() -> Dict[str, Any]:
    return {
        "version": "stage7h-v1",
        "ai_runtime_call_enabled": False,
        "deterministic_checks": [
            "review_id must match request.review_id",
            "suggested_action must be one of allowed enum",
            "suggested_row_ids must be subset of request.candidate_rows.row_id",
            "accept_one must contain exactly one suggested_row_id",
            "merge_same_value must contain one or more suggested_row_ids",
            "suggested_value/unit/year must match selected candidate row(s) when action is accept_one",
            "EPS/每股收益 suggested_unit must not be ratio or %",
            "confidence must be in [0,1]",
            "requires_human_approval must be true for true_value_conflict/high-risk ambiguity",
            "if no valid evidence, action must be keep_manual_review",
        ],
        "fallback_rules": [
            "validation failure => keep_manual_review",
            "low confidence (<0.60) => keep_manual_review",
            "conflicting evidence without clear priority => keep_manual_review",
        ],
        "audit_log_fields": [
            "review_id",
            "conflict_group_id",
            "input_candidate_row_count",
            "suggested_action",
            "suggested_row_ids",
            "validation_pass",
            "validation_errors",
            "requires_human_approval",
            "timestamp",
        ],
    }


def _pick_case_keys(remain: pd.DataFrame, case_count: int = 5) -> List[str]:
    group_col = "analysis_key" if "analysis_key" in remain.columns else "key"
    grp = remain.groupby(group_col, dropna=False)

    meta = []
    for k, g in grp:
        metric = _norm(g.iloc[0].get("standard_metric"))
        reason = _norm(g.iloc[0].get("manual_review_reason"))
        meta.append((str(k), metric, reason, len(g)))

    meta = sorted(meta, key=lambda x: (-x[3], x[0]))

    picked: List[str] = []
    seen_metric = set()
    for k, metric, _reason, _n in meta:
        if metric and metric not in seen_metric:
            picked.append(k)
            seen_metric.add(metric)
        if len(picked) >= case_count:
            return picked

    for k, _metric, _reason, _n in meta:
        if k not in picked:
            picked.append(k)
        if len(picked) >= case_count:
            break

    return picked[:case_count]


def _make_request(review_id: str, group_key: str, g: pd.DataFrame, policy_context: Dict[str, Any]) -> Dict[str, Any]:
    candidates = []
    for idx, (_, r) in enumerate(g.iterrows(), start=1):
        row_id = f"{review_id}_row_{idx:02d}"
        candidates.append(
            {
                "row_id": row_id,
                "statement_type": _norm(r.get("statement_type_for_priority") or r.get("statement_type")),
                "raw_metric_name": _norm(r.get("raw_metric_name")),
                "normalized_metric_name": _norm(r.get("standard_metric") or r.get("normalized_metric_name")),
                "year": _norm(r.get("year")),
                "value": _norm(r.get("final_value") or r.get("value")),
                "unit": _norm(r.get("final_unit") or r.get("inferred_unit")),
                "source_page": _norm(r.get("page_number")),
                "source_table_id": _norm(r.get("raw_table_id")),
                "source_text_excerpt": _norm(r.get("source_text_excerpt")),
                "extraction_confidence": _norm(r.get("extraction_confidence")),
                "unit_confidence": _norm(r.get("unit_confidence")),
                "classification_confidence": _norm(r.get("classification_confidence")),
            }
        )

    return {
        "review_id": review_id,
        "source_pdf": _norm(g.iloc[0].get("source_pdf")),
        "conflict_group_id": group_key,
        "manual_review_reason": _norm(g.iloc[0].get("manual_review_reason") or "needs_human_business_judgement"),
        "candidate_rows": candidates,
        "current_policy_context": {
            "policy_stage": "stage7g",
            "deterministic_suggestions": policy_context.get("new_deterministic_suggestions", []),
            "fallback": "if uncertain keep_manual_review",
        },
        "known_rules": {
            "eps_unit": "元/股",
            "do_not_use_ratio_for_eps": True,
        },
    }


def _extract_numeric_tokens_after_label(excerpt: str, raw_metric_name: str) -> List[float]:
    tokens = [_norm(t) for t in _norm(excerpt).split("|")]
    if not tokens:
        return []
    label = _norm(raw_metric_name)
    start = -1
    for i, t in enumerate(tokens):
        if label and label in t:
            start = i
            break
    if start < 0:
        return []
    vals: List[float] = []
    for t in tokens[start + 1 :]:
        c = t.replace(",", "").replace("%", "").strip()
        if not c:
            continue
        try:
            vals.append(float(c))
        except Exception:
            break
    return vals


def _mock_response(req: Dict[str, Any]) -> Dict[str, Any]:
    metric = _norm(req["candidate_rows"][0].get("normalized_metric_name")) if req.get("candidate_rows") else ""
    rows = req.get("candidate_rows", [])

    # evidence alignment: value appears in the metric-local numeric segment
    aligned_row_ids = []
    for r in rows:
        vals = _extract_numeric_tokens_after_label(r.get("source_text_excerpt", ""), r.get("raw_metric_name", ""))
        rv = _to_float(r.get("value", ""))
        ok = False
        if not pd.isna(rv):
            for x in vals:
                if abs(rv - x) <= 1e-9:
                    ok = True
                    break
        if ok:
            aligned_row_ids.append(r.get("row_id"))

    action = "keep_manual_review"
    suggested_ids: List[str] = []
    confidence = 0.42
    reason = "Multiple candidates remain ambiguous under deterministic evidence."
    risk_flags = ["true_value_conflict", "needs_human_business_judgement"]

    if len(aligned_row_ids) == 1:
        action = "accept_one"
        suggested_ids = [aligned_row_ids[0]]
        confidence = 0.72
        reason = "Exactly one candidate aligns with metric-local numeric evidence in source excerpt."
        risk_flags = ["true_value_conflict", "human_approval_required"]

    selected = None
    if suggested_ids:
        for r in rows:
            if r.get("row_id") == suggested_ids[0]:
                selected = r
                break

    suggested_metric_name = metric
    suggested_year = _norm(selected.get("year")) if selected else ""
    suggested_value = _norm(selected.get("value")) if selected else ""
    suggested_unit = _norm(selected.get("unit")) if selected else ""

    if metric in EPS_ALIASES and suggested_unit in {"ratio", "%"}:
        action = "keep_manual_review"
        suggested_ids = []
        suggested_year = ""
        suggested_value = ""
        suggested_unit = ""
        confidence = min(confidence, 0.35)
        reason = "EPS unit safety rule triggered; ratio/% suggestion is forbidden."
        risk_flags = ["eps_unit_safety_block", "needs_human_business_judgement"]

    return {
        "review_id": req["review_id"],
        "suggested_action": action,
        "suggested_row_ids": suggested_ids,
        "suggested_metric_name": suggested_metric_name,
        "suggested_year": suggested_year,
        "suggested_value": suggested_value,
        "suggested_unit": suggested_unit,
        "confidence": round(float(confidence), 4),
        "reasoning_summary": reason,
        "risk_flags": risk_flags,
        "requires_human_approval": True,
    }


def _validate(req: Dict[str, Any], resp: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []

    if _norm(req.get("review_id")) != _norm(resp.get("review_id")):
        errors.append("review_id_mismatch")

    action = _norm(resp.get("suggested_action"))
    if action not in ALLOWED_ACTIONS:
        errors.append("invalid_action")

    req_row_ids = {c.get("row_id") for c in req.get("candidate_rows", [])}
    resp_row_ids = list(resp.get("suggested_row_ids", []))
    for rid in resp_row_ids:
        if rid not in req_row_ids:
            errors.append("suggested_row_id_not_in_candidates")
            break

    if action == "accept_one" and len(resp_row_ids) != 1:
        errors.append("accept_one_requires_one_row")

    if action == "merge_same_value" and len(resp_row_ids) < 1:
        errors.append("merge_requires_rows")

    conf = resp.get("confidence")
    try:
        confv = float(conf)
        if confv < 0 or confv > 1:
            errors.append("confidence_out_of_range")
    except Exception:
        errors.append("confidence_not_numeric")

    metric = _norm(req.get("candidate_rows", [{}])[0].get("normalized_metric_name")) if req.get("candidate_rows") else ""
    if metric in EPS_ALIASES and _norm(resp.get("suggested_unit")) in {"ratio", "%"}:
        errors.append("eps_ratio_forbidden")

    if action == "accept_one" and resp_row_ids:
        row_map = {c.get("row_id"): c for c in req.get("candidate_rows", [])}
        c = row_map.get(resp_row_ids[0], {})
        if _norm(resp.get("suggested_value")) != _norm(c.get("value")):
            errors.append("suggested_value_not_from_selected_row")
        if _norm(resp.get("suggested_unit")) != _norm(c.get("unit")):
            errors.append("suggested_unit_not_from_selected_row")
        if _norm(resp.get("suggested_year")) != _norm(c.get("year")):
            errors.append("suggested_year_not_from_selected_row")

    if not bool(resp.get("requires_human_approval", False)):
        errors.append("requires_human_approval_must_be_true")

    return {
        "review_id": _norm(req.get("review_id")),
        "validation_pass": len(errors) == 0,
        "validation_errors": errors,
    }


def _build_runtime_plan() -> str:
    return """# Stage7H Runtime Integration Plan (Design Only)

## Goal
Integrate AI-assisted suggestion layer between manual-review queue and sandbox clean preview generation, with strict deterministic validation and human approval.

## Proposed entrypoint
`python tools/run_stage7i_ai_runtime_dry_run.py --input output/stage7g_manual_review_reduction_sandbox --output output/stage7i_ai_runtime_dry_run`

## Pipeline placement
1. Build deterministic reduced preview (existing Stage 7G flow).
2. Build manual review evidence package per conflict group.
3. Generate AI request payloads.
4. Call AI runtime adapter (Stage 7I; mock in dry-run mode).
5. Validate AI responses using deterministic rules.
6. Route validated suggestions to `ai_suggestion_queue` (still requires human approval).
7. Keep rejected/invalid suggestions in `manual_review_queue`.
8. Produce audit logs and stage summary.

## Safety gates
- AI cannot write production 06.
- AI cannot modify formal rules.
- True conflicts remain human-approved.
- EPS unit guard (元/股 only).
- Non-traceable suggestions are automatically rejected.

## Audit artifacts
- ai_review_requests.jsonl
- ai_review_responses.jsonl
- ai_validation_results.xlsx/json
- ai_suggestion_audit_log.xlsx
- manual_approval_queue.xlsx

## Human-in-the-loop protocol
- Reviewer accepts/rejects per review_id.
- Any rejected item returns to manual queue.
- Accepted items can be merged into sandbox preview only.
"""


def main() -> int:
    required = [IN_SUMMARY, IN_REMAIN, IN_CLASSIFIED, IN_POLICY_SUGGEST, IN_REDUCED_PREVIEW, IN_STAGE7D_CLASSIFIED]
    for p in required:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    before = _snapshot_guard()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    s7g_summary, remain, _classified, policy_suggest, reduced_preview, _stage7d_cls = _load_inputs()

    req_schema = _build_request_schema()
    resp_schema = _build_response_schema()
    prompt_template = _build_prompt_template()
    validation_rules = _build_validation_rules()
    runtime_plan = _build_runtime_plan()

    group_col = "analysis_key" if "analysis_key" in remain.columns else "key"
    case_keys = _pick_case_keys(remain, case_count=5)

    mock_requests: List[Dict[str, Any]] = []
    mock_responses: List[Dict[str, Any]] = []
    mock_validation: List[Dict[str, Any]] = []

    for i, k in enumerate(case_keys, start=1):
        g = remain[remain[group_col].map(_norm) == _norm(k)].copy()
        review_id = f"stage7h_review_{i:03d}"
        req = _make_request(review_id, _norm(k), g, policy_suggest)
        resp = _mock_response(req)
        val = _validate(req, resp)

        mock_requests.append(req)
        mock_responses.append(resp)
        mock_validation.append(val)

    OUT_REQ_SCHEMA.write_text(json.dumps(req_schema, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_RESP_SCHEMA.write_text(json.dumps(resp_schema, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_PROMPT.write_text(prompt_template, encoding="utf-8")
    OUT_VALIDATION.write_text(json.dumps(validation_rules, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_RUNTIME_PLAN.write_text(runtime_plan, encoding="utf-8")

    with open(OUT_MOCK_REQ, "w", encoding="utf-8") as f:
        for item in mock_requests:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    with open(OUT_MOCK_RESP, "w", encoding="utf-8") as f:
        for item in mock_responses:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    # Safety snapshot compare
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
        "stage": "stage7h_ai_assisted_review_design",
        "mode": "design_only_no_api_call",
        "based_on_stage7g_commit": "20e3f3713b1d599d676aa9012120f91be2eae74f",
        "input_remaining_manual_review_rows": int(len(remain)),
        "ai_runtime_call_enabled": False,
        "mock_review_case_count": int(len(mock_requests)),
        "request_schema_generated": True,
        "response_schema_generated": True,
        "prompt_template_generated": True,
        "validation_rules_generated": True,
        "runtime_integration_plan_generated": True,
        "production_files_modified": bool(production_files_modified),
        "official_02b_modified": bool(official_02b_modified),
        "formal_rules_modified": bool(formal_rules_modified),
        "standardizer_modified": bool(standardizer_modified),
        "release_package_modified": bool(release_package_modified),
        "check_delivery_state_overall_status": overall_status,
        "ready_for_stage7i_ai_runtime_dry_run": False,
    }

    summary["ready_for_stage7i_ai_runtime_dry_run"] = bool(
        summary["mock_review_case_count"] == 5
        and summary["request_schema_generated"]
        and summary["response_schema_generated"]
        and summary["prompt_template_generated"]
        and summary["validation_rules_generated"]
        and summary["runtime_integration_plan_generated"]
        and not summary["production_files_modified"]
        and not summary["official_02b_modified"]
        and not summary["formal_rules_modified"]
        and not summary["standardizer_modified"]
        and not summary["release_package_modified"]
        and summary["check_delivery_state_overall_status"] == "PASS"
    )

    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    reason_dist = remain["manual_review_reason"].map(_norm).value_counts().to_dict() if "manual_review_reason" in remain.columns else {}
    validation_pass_count = sum(1 for r in mock_validation if r.get("validation_pass"))
    validation_fail_count = len(mock_validation) - validation_pass_count

    report_lines = [
        "# Stage 7H AI-Assisted Manual Review Design",
        "",
        "## Background",
        f"- Stage7G remaining_manual_review_rows: {len(remain)}",
        "- Current goal: design-only, no real API call, no production update.",
        "",
        "## Design Scope",
        "1. AI review request schema",
        "2. AI review response schema",
        "3. Prompt template",
        "4. Validation rules",
        "5. Runtime integration plan",
        "6. Mock request/response set (5 cases)",
        "",
        "## Input Snapshot",
        f"- reduced_clean_06_preview_rows: {len(reduced_preview)}",
        f"- manual_review_reason_distribution: {json.dumps(reason_dist, ensure_ascii=False)}",
        "",
        "## Mock Case Validation",
        f"- validation_pass_count: {validation_pass_count}",
        f"- validation_fail_count: {validation_fail_count}",
        "",
        "## Safety Rules",
        "- AI cannot write production 06.",
        "- AI cannot modify formal rules.",
        "- EPS/每股收益 cannot use ratio/% unit.",
        "- If evidence is insufficient, keep_manual_review.",
        "- All suggestions require human approval.",
        "",
        "## Verification",
        f"- check_delivery_state_overall_status: {overall_status}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
        "",
        "## Decision",
        f"- ready_for_stage7i_ai_runtime_dry_run: {summary['ready_for_stage7i_ai_runtime_dry_run']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"stage7h_summary_json: {OUT_SUMMARY}")
    print(f"stage7h_report_md: {OUT_REPORT}")
    print(f"stage7h_ready_for_stage7i_ai_runtime_dry_run: {summary['ready_for_stage7i_ai_runtime_dry_run']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
