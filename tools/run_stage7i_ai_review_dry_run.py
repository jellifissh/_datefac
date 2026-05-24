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
STAGE7H_DIR = BASE_DIR / "output" / "stage7h_ai_assisted_review_design"
STAGE7G_DIR = BASE_DIR / "output" / "stage7g_manual_review_reduction_sandbox"
STAGE7D_DIR = BASE_DIR / "output" / "stage7d_pipeline_sandbox"
OUT_DIR = BASE_DIR / "output" / "stage7i_ai_runtime_dry_run"

IN_S7H_SUMMARY = STAGE7H_DIR / "187_stage7h_ai_review_design_summary.json"
IN_REQ_SCHEMA = STAGE7H_DIR / "187_stage7h_ai_review_request_schema.json"
IN_RESP_SCHEMA = STAGE7H_DIR / "187_stage7h_ai_review_response_schema.json"
IN_PROMPT = STAGE7H_DIR / "187_stage7h_prompt_template.md"
IN_VALIDATION_RULES = STAGE7H_DIR / "187_stage7h_ai_validation_rules.json"

IN_REMAIN = STAGE7G_DIR / "186_stage7g_remaining_manual_review.xlsx"
IN_REDUCED_PREVIEW = STAGE7G_DIR / "186_stage7g_reduced_clean_06_preview.xlsx"
IN_STAGE7D_CLASSIFIED = STAGE7D_DIR / "183_stage7d_classified_structured_table.xlsx"

OUT_SUMMARY = OUT_DIR / "188_stage7i_ai_runtime_dry_run_summary.json"
OUT_REPORT = OUT_DIR / "188_stage7i_ai_runtime_dry_run_report.md"
OUT_REQUESTS = OUT_DIR / "188_stage7i_ai_review_requests.jsonl"
OUT_RESPONSES = OUT_DIR / "188_stage7i_mock_ai_responses.jsonl"
OUT_SUGGEST = OUT_DIR / "188_stage7i_ai_suggestion_queue.xlsx"
OUT_REJECTED = OUT_DIR / "188_stage7i_ai_rejected_suggestions.xlsx"
OUT_AUDIT = OUT_DIR / "188_stage7i_ai_validation_audit.xlsx"
OUT_PREVIEW = OUT_DIR / "188_stage7i_ai_assisted_clean_preview_dry_run.xlsx"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

EPS_ALIASES = {"EPS", "每股收益"}
LOW_CONF_THRESHOLD = 0.60


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


def _extract_metric_section_values(excerpt: str, raw_metric_name: str) -> List[float]:
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


def _build_requests(remain: pd.DataFrame, req_schema: Dict[str, Any], validation_ctx: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str]:
    group_col = "analysis_key" if "analysis_key" in remain.columns else "key"
    requests: List[Dict[str, Any]] = []

    for idx, (group_key, g) in enumerate(remain.groupby(group_col, dropna=False), start=1):
        g = g.copy().reset_index(drop=True)
        review_id = f"stage7i_review_{idx:04d}"

        candidates: List[Dict[str, Any]] = []
        for i, row in g.iterrows():
            row_id = f"{review_id}_row_{i+1:02d}"
            candidates.append(
                {
                    "row_id": row_id,
                    "statement_type": _norm(row.get("statement_type_for_priority") or row.get("statement_type")),
                    "raw_metric_name": _norm(row.get("raw_metric_name")),
                    "normalized_metric_name": _norm(row.get("standard_metric") or row.get("normalized_metric_name")),
                    "year": _norm(row.get("year")),
                    "value": _norm(row.get("final_value") or row.get("value")),
                    "unit": _norm(row.get("final_unit") or row.get("inferred_unit")),
                    "source_page": _norm(row.get("page_number")),
                    "source_table_id": _norm(row.get("raw_table_id")),
                    "source_text_excerpt": _norm(row.get("source_text_excerpt")),
                    "extraction_confidence": _norm(row.get("extraction_confidence")),
                    "unit_confidence": _norm(row.get("unit_confidence")),
                    "classification_confidence": _norm(row.get("classification_confidence")),
                }
            )

        req = {
            "review_id": review_id,
            "source_pdf": _norm(g.iloc[0].get("source_pdf")),
            "conflict_group_id": _norm(group_key),
            "manual_review_reason": _norm(g.iloc[0].get("manual_review_reason") or "needs_human_business_judgement"),
            "candidate_rows": candidates,
            "current_policy_context": {
                "stage": "stage7g",
                "runtime_mode": "mock_no_external_api_call",
                "validation_context": validation_ctx,
            },
            "known_rules": {
                "eps_unit": "元/股",
                "do_not_use_ratio_for_eps": True,
            },
        }
        requests.append(req)

    granularity_note = f"grouped_by={group_col}; input_rows={len(remain)}; review_request_count={len(requests)}"
    return requests, granularity_note


def _mock_response(req: Dict[str, Any], reduced_preview_keys: set) -> Dict[str, Any]:
    rows = req.get("candidate_rows", [])
    metric = _norm(rows[0].get("normalized_metric_name")) if rows else ""
    key = _norm(req.get("conflict_group_id"))

    # default conservative output
    action = "keep_manual_review"
    suggested_row_ids: List[str] = []
    suggested_value = ""
    suggested_unit = ""
    suggested_year = ""
    confidence = 0.45
    reasoning = "Ambiguous evidence; keep manual review."
    risk_flags = ["manual_review_required"]

    if len(rows) == 1 and key in reduced_preview_keys:
        # this candidate is residual competing row after deterministic selection
        r = rows[0]
        action = "exclude"
        suggested_row_ids = [_norm(r.get("row_id"))]
        suggested_value = _norm(r.get("value"))
        suggested_unit = _norm(r.get("unit"))
        suggested_year = _norm(r.get("year"))
        confidence = 0.78
        reasoning = "Residual conflicting row in group already represented by reduced preview; suggest exclude from AI-assisted append."
        risk_flags = ["true_value_conflict", "exclude_residual_candidate"]
    elif len(rows) > 1:
        # try merge when all same value+unit
        vset = {_norm(r.get("value")) for r in rows}
        uset = {_norm(r.get("unit")) for r in rows}
        if len(vset) == 1 and len(uset) == 1:
            action = "merge_same_value"
            suggested_row_ids = [_norm(r.get("row_id")) for r in rows]
            suggested_value = next(iter(vset))
            suggested_unit = next(iter(uset))
            suggested_year = _norm(rows[0].get("year"))
            confidence = 0.74
            reasoning = "All candidates share same value and unit; merge is safe in sandbox."
            risk_flags = ["requires_human_confirmation"]
        else:
            # evidence extraction: if exactly one candidate aligns in metric section
            aligned = []
            for r in rows:
                vals = _extract_metric_section_values(_norm(r.get("source_text_excerpt")), _norm(r.get("raw_metric_name")))
                rv = _to_float(r.get("value"))
                ok = False
                if not pd.isna(rv):
                    for x in vals:
                        if abs(rv - x) <= 1e-9:
                            ok = True
                            break
                if ok:
                    aligned.append(r)

            # true_value_conflict default not auto accept; still keep manual
            if len(aligned) == 1:
                confidence = 0.58
                reasoning = "One candidate aligns with metric-section evidence, but conflict class defaults to manual approval."
                risk_flags = ["true_value_conflict", "human_approval_required"]

    if metric in EPS_ALIASES and _norm(suggested_unit) in {"ratio", "%"}:
        action = "keep_manual_review"
        suggested_row_ids = []
        suggested_value = ""
        suggested_unit = ""
        suggested_year = ""
        confidence = min(confidence, 0.35)
        reasoning = "EPS unit safety rule blocked ratio/% suggestion."
        risk_flags = ["eps_unit_safety_block", "manual_review_required"]

    return {
        "review_id": _norm(req.get("review_id")),
        "suggested_action": action,
        "suggested_row_ids": suggested_row_ids,
        "suggested_metric_name": metric,
        "suggested_year": suggested_year,
        "suggested_value": suggested_value,
        "suggested_unit": suggested_unit,
        "confidence": round(float(confidence), 4),
        "reasoning_summary": reasoning,
        "risk_flags": risk_flags,
        "requires_human_approval": True,
    }


def _validate_schema(resp: Dict[str, Any], resp_schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    req_fields = resp_schema.get("required", [])
    props = resp_schema.get("properties", {})

    for f in req_fields:
        if f not in resp:
            errors.append(f"missing_required:{f}")

    # basic type checks for known properties
    type_map = {
        "string": str,
        "number": (int, float),
        "array": list,
        "boolean": bool,
    }

    for f, spec in props.items():
        if f not in resp:
            continue
        et = spec.get("type")
        if et in type_map and not isinstance(resp[f], type_map[et]):
            errors.append(f"type_mismatch:{f}:{et}")

    # enum check
    act_spec = props.get("suggested_action", {})
    if "enum" in act_spec and _norm(resp.get("suggested_action")) not in set(act_spec["enum"]):
        errors.append("enum_violation:suggested_action")

    conf = resp.get("confidence")
    try:
        confv = float(conf)
        if confv < 0 or confv > 1:
            errors.append("confidence_out_of_range")
    except Exception:
        errors.append("confidence_not_numeric")

    return len(errors) == 0, errors


def _validate_response(req: Dict[str, Any], resp: Dict[str, Any], validation_rules: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    req_rows = req.get("candidate_rows", [])
    req_row_ids = {_norm(r.get("row_id")) for r in req_rows}
    req_reason = _norm(req.get("manual_review_reason"))
    metric = _norm(req_rows[0].get("normalized_metric_name")) if req_rows else ""

    if _norm(req.get("review_id")) != _norm(resp.get("review_id")):
        errors.append("review_id_mismatch")

    action = _norm(resp.get("suggested_action"))
    row_ids = [_norm(x) for x in resp.get("suggested_row_ids", [])]

    for rid in row_ids:
        if rid not in req_row_ids:
            errors.append("suggested_row_id_not_in_request")
            break

    if action == "accept_one" and len(row_ids) != 1:
        errors.append("accept_one_requires_single_row")
    if action in {"merge_same_value", "exclude"} and len(row_ids) < 1:
        errors.append(f"{action}_requires_row_ids")

    # no hallucinated values
    selected_rows = [r for r in req_rows if _norm(r.get("row_id")) in set(row_ids)]
    if action in {"accept_one", "merge_same_value", "exclude"} and selected_rows:
        sv = _norm(resp.get("suggested_value"))
        su = _norm(resp.get("suggested_unit"))
        sy = _norm(resp.get("suggested_year"))
        values = {_norm(r.get("value")) for r in selected_rows}
        units = {_norm(r.get("unit")) for r in selected_rows}
        years = {_norm(r.get("year")) for r in selected_rows}
        if sv and sv not in values:
            errors.append("suggested_value_not_from_candidates")
        if su and su not in units:
            errors.append("suggested_unit_not_from_candidates")
        if sy and sy not in years:
            errors.append("suggested_year_not_from_candidates")

    if metric in EPS_ALIASES and _norm(resp.get("suggested_unit")) in {"ratio", "%"}:
        errors.append("eps_ratio_forbidden")

    # true_value_conflict default cannot auto-accept
    if req_reason == "true_value_conflict" and action == "accept_one":
        errors.append("true_value_conflict_auto_accept_forbidden")

    try:
        conf = float(resp.get("confidence"))
        if conf < LOW_CONF_THRESHOLD and not bool(resp.get("requires_human_approval", False)):
            errors.append("low_confidence_requires_human_approval")
    except Exception:
        errors.append("confidence_invalid")

    if not bool(resp.get("requires_human_approval", False)):
        errors.append("requires_human_approval_must_be_true")

    return len(errors) == 0, errors


def _conflict_stats(df: pd.DataFrame) -> Dict[str, int]:
    if df.empty:
        return {
            "duplicate_key_count_after_preview": 0,
            "value_mismatch_count_after_preview": 0,
            "unit_conflict_count_after_preview": 0,
            "year_conflict_count_after_preview": 0,
        }

    w = df.copy()
    w["asset_package"] = w["asset_package"].map(_norm)
    w["standard_metric"] = w["standard_metric"].map(_norm)
    w["year"] = w["year"].map(_norm)
    w["final_value"] = w["final_value"].map(_norm)
    w["final_unit"] = w["final_unit"].map(_norm)
    w["_key"] = w["asset_package"] + "||" + w["standard_metric"] + "||" + w["year"]

    duplicate_key_count = int(w["_key"].duplicated().sum())
    value_mismatch_count = 0
    unit_conflict_count = 0

    for _, g in w.groupby("_key", dropna=False):
        if g["final_value"].nunique() > 1:
            value_mismatch_count += 1
        if g["final_unit"].nunique() > 1:
            unit_conflict_count += 1

    year_conflict_count = 0
    for _, g in w.groupby(["asset_package", "standard_metric"], dropna=False):
        ys = [y for y in g["year"].tolist() if y]
        if len(ys) != len(set(ys)):
            year_conflict_count += 1

    return {
        "duplicate_key_count_after_preview": duplicate_key_count,
        "value_mismatch_count_after_preview": value_mismatch_count,
        "unit_conflict_count_after_preview": unit_conflict_count,
        "year_conflict_count_after_preview": year_conflict_count,
    }


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for s, df in sheets.items():
            df.to_excel(writer, sheet_name=s[:31], index=False)


def main() -> int:
    required = [
        IN_S7H_SUMMARY,
        IN_REQ_SCHEMA,
        IN_RESP_SCHEMA,
        IN_PROMPT,
        IN_VALIDATION_RULES,
        IN_REMAIN,
        IN_REDUCED_PREVIEW,
        IN_STAGE7D_CLASSIFIED,
    ]
    for p in required:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    before = _snapshot_guard()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    s7h_summary = json.loads(IN_S7H_SUMMARY.read_text(encoding="utf-8"))
    req_schema = json.loads(IN_REQ_SCHEMA.read_text(encoding="utf-8"))
    resp_schema = json.loads(IN_RESP_SCHEMA.read_text(encoding="utf-8"))
    validation_rules = json.loads(IN_VALIDATION_RULES.read_text(encoding="utf-8"))

    remain = pd.read_excel(IN_REMAIN, sheet_name="remaining_manual_review").fillna("")
    reduced_preview = pd.read_excel(IN_REDUCED_PREVIEW, sheet_name="reduced_clean_06_preview").fillna("")

    reduced_keys = set(
        reduced_preview["asset_package"].map(_norm)
        + "||"
        + reduced_preview["standard_metric"].map(_norm)
        + "||"
        + reduced_preview["year"].map(_norm)
    )

    requests, granularity_note = _build_requests(remain, req_schema, validation_rules)
    responses: List[Dict[str, Any]] = []

    audit_rows: List[Dict[str, Any]] = []
    suggestion_rows: List[Dict[str, Any]] = []
    rejected_rows: List[Dict[str, Any]] = []

    for req in requests:
        resp = _mock_response(req, reduced_keys)
        responses.append(resp)

        schema_ok, schema_errors = _validate_schema(resp, resp_schema)
        logic_ok, logic_errors = _validate_response(req, resp, validation_rules)
        all_ok = schema_ok and logic_ok

        action = _norm(resp.get("suggested_action"))
        requires_human = bool(resp.get("requires_human_approval", False))

        row = {
            "review_id": _norm(req.get("review_id")),
            "conflict_group_id": _norm(req.get("conflict_group_id")),
            "candidate_row_count": int(len(req.get("candidate_rows", []))),
            "suggested_action": action,
            "suggested_row_ids": "|".join(resp.get("suggested_row_ids", [])),
            "confidence": resp.get("confidence"),
            "requires_human_approval": requires_human,
            "schema_valid": schema_ok,
            "logic_valid": logic_ok,
            "validation_pass": all_ok,
            "schema_errors": "|".join(schema_errors),
            "logic_errors": "|".join(logic_errors),
            "reasoning_summary": _norm(resp.get("reasoning_summary")),
            "risk_flags": "|".join(resp.get("risk_flags", [])),
        }
        audit_rows.append(row)

        if all_ok and action != "keep_manual_review":
            # validated actionable suggestion
            suggestion_rows.append(
                {
                    **row,
                    "suggested_metric_name": _norm(resp.get("suggested_metric_name")),
                    "suggested_year": _norm(resp.get("suggested_year")),
                    "suggested_value": _norm(resp.get("suggested_value")),
                    "suggested_unit": _norm(resp.get("suggested_unit")),
                }
            )
        else:
            rej_reason = ""
            if not all_ok:
                rej_reason = "validation_failed"
            elif action == "keep_manual_review":
                rej_reason = "non_actionable_keep_manual_review"
            rejected_rows.append(
                {
                    **row,
                    "rejection_reason": rej_reason,
                    "suggested_metric_name": _norm(resp.get("suggested_metric_name")),
                    "suggested_year": _norm(resp.get("suggested_year")),
                    "suggested_value": _norm(resp.get("suggested_value")),
                    "suggested_unit": _norm(resp.get("suggested_unit")),
                }
            )

    # Build assisted preview: Stage7I keeps Stage7G reduced preview unchanged in this mock runtime
    assisted_preview = reduced_preview.copy()
    conflict_after = _conflict_stats(assisted_preview)

    eps_detected_count = int(assisted_preview[assisted_preview["standard_metric"].map(_norm).isin(EPS_ALIASES)].shape[0])
    bad_eps_ratio_count = int(
        assisted_preview[
            assisted_preview["standard_metric"].map(_norm).isin(EPS_ALIASES)
            & assisted_preview["final_unit"].map(_norm).isin({"ratio", "%"})
        ].shape[0]
    )

    # write jsonl
    with open(OUT_REQUESTS, "w", encoding="utf-8") as f:
        for r in requests:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(OUT_RESPONSES, "w", encoding="utf-8") as f:
        for r in responses:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    sug_df = pd.DataFrame(suggestion_rows).fillna("")
    rej_df = pd.DataFrame(rejected_rows).fillna("")
    aud_df = pd.DataFrame(audit_rows).fillna("")

    _write_excel(OUT_SUGGEST, {"ai_suggestion_queue": sug_df})
    _write_excel(OUT_REJECTED, {"ai_rejected_suggestions": rej_df})
    _write_excel(OUT_AUDIT, {"ai_validation_audit": aud_df})
    _write_excel(OUT_PREVIEW, {"ai_assisted_clean_preview": assisted_preview})

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

    schema_valid_count = int(aud_df["schema_valid"].astype(bool).sum()) if not aud_df.empty else 0
    schema_invalid_count = int(len(aud_df) - schema_valid_count)
    validated_suggestion_count = int(len(sug_df))
    rejected_suggestion_count = int(len(rej_df))
    requires_human_approval_count = int(aud_df["requires_human_approval"].astype(bool).sum()) if not aud_df.empty else 0

    summary = {
        "stage": "stage7i_ai_runtime_dry_run",
        "mode": "mock_no_external_api_call",
        "based_on_stage7h_commit": "754e26300d0840099fb2c6f470252f6689d1bf7c",
        "input_remaining_manual_review_rows": int(len(remain)),
        "ai_runtime_call_enabled": False,
        "external_api_called": False,
        "review_request_count": int(len(requests)),
        "mock_response_count": int(len(responses)),
        "schema_valid_response_count": int(schema_valid_count),
        "schema_invalid_response_count": int(schema_invalid_count),
        "validated_suggestion_count": int(validated_suggestion_count),
        "rejected_suggestion_count": int(rejected_suggestion_count),
        "requires_human_approval_count": int(requires_human_approval_count),
        "ai_assisted_clean_preview_rows": int(len(assisted_preview)),
        "duplicate_key_count_after_preview": int(conflict_after["duplicate_key_count_after_preview"]),
        "value_mismatch_count_after_preview": int(conflict_after["value_mismatch_count_after_preview"]),
        "unit_conflict_count_after_preview": int(conflict_after["unit_conflict_count_after_preview"]),
        "year_conflict_count_after_preview": int(conflict_after["year_conflict_count_after_preview"]),
        "eps_detected_count": int(eps_detected_count),
        "bad_eps_ratio_count": int(bad_eps_ratio_count),
        "production_files_modified": bool(production_files_modified),
        "official_02b_modified": bool(official_02b_modified),
        "formal_rules_modified": bool(formal_rules_modified),
        "standardizer_modified": bool(standardizer_modified),
        "release_package_modified": bool(release_package_modified),
        "check_delivery_state_overall_status": overall_status,
        "request_granularity_note": granularity_note,
        "ready_for_stage7j_real_ai_api_integration_design": False,
    }

    summary["ready_for_stage7j_real_ai_api_integration_design"] = bool(
        summary["ai_runtime_call_enabled"] is False
        and summary["external_api_called"] is False
        and summary["review_request_count"] > 0
        and summary["mock_response_count"] == summary["review_request_count"]
        and summary["schema_invalid_response_count"] == 0
        and summary["duplicate_key_count_after_preview"] == 0
        and summary["value_mismatch_count_after_preview"] == 0
        and summary["unit_conflict_count_after_preview"] == 0
        and summary["year_conflict_count_after_preview"] == 0
        and summary["bad_eps_ratio_count"] == 0
        and not summary["production_files_modified"]
        and not summary["official_02b_modified"]
        and not summary["formal_rules_modified"]
        and not summary["standardizer_modified"]
        and not summary["release_package_modified"]
        and summary["check_delivery_state_overall_status"] == "PASS"
    )

    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    report_lines = [
        "# Stage 7I AI Runtime Dry Run (Mock Mode)",
        "",
        "## Scope",
        "- Mock runtime only (no external AI API call).",
        "- No production update, no formal rule update.",
        "",
        "## Input",
        f"- input_remaining_manual_review_rows: {len(remain)}",
        f"- request_granularity: {granularity_note}",
        "",
        "## Runtime Result",
        f"- review_request_count: {summary['review_request_count']}",
        f"- mock_response_count: {summary['mock_response_count']}",
        f"- schema_valid_response_count: {summary['schema_valid_response_count']}",
        f"- schema_invalid_response_count: {summary['schema_invalid_response_count']}",
        f"- validated_suggestion_count: {summary['validated_suggestion_count']}",
        f"- rejected_suggestion_count: {summary['rejected_suggestion_count']}",
        f"- requires_human_approval_count: {summary['requires_human_approval_count']}",
        "",
        "## Preview",
        f"- ai_assisted_clean_preview_rows: {summary['ai_assisted_clean_preview_rows']}",
        f"- duplicate/value/unit/year: {summary['duplicate_key_count_after_preview']}/{summary['value_mismatch_count_after_preview']}/{summary['unit_conflict_count_after_preview']}/{summary['year_conflict_count_after_preview']}",
        f"- eps_detected_count: {summary['eps_detected_count']}",
        f"- bad_eps_ratio_count: {summary['bad_eps_ratio_count']}",
        "",
        "## Safety",
        f"- ai_runtime_call_enabled: {summary['ai_runtime_call_enabled']}",
        f"- external_api_called: {summary['external_api_called']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        "",
        "## Decision",
        f"- ready_for_stage7j_real_ai_api_integration_design: {summary['ready_for_stage7j_real_ai_api_integration_design']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"stage7i_summary_json: {OUT_SUMMARY}")
    print(f"stage7i_report_md: {OUT_REPORT}")
    print(f"stage7i_ready_for_stage7j_real_ai_api_integration_design: {summary['ready_for_stage7j_real_ai_api_integration_design']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
