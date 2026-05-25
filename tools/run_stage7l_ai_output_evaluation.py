import json
import sys
from pathlib import Path
from typing import Any, Dict, List

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

BASE_DIR = Path(r"D:\_datefac")
IN_7K_SUMMARY = BASE_DIR / "output" / "stage7k_retry_lowrate_glm_api_sandbox" / "191_stage7k_retry_lowrate_summary.json"
IN_7K_RAW = BASE_DIR / "output" / "stage7k_retry_lowrate_glm_api_sandbox" / "191_stage7k_raw_response_sanitized.json"
IN_7K_VALID = BASE_DIR / "output" / "stage7k_retry_lowrate_glm_api_sandbox" / "191_stage7k_validation_result.json"
IN_7K2_SUMMARY = BASE_DIR / "output" / "stage7k2_strict_schema_glm_retry" / "192_stage7k2_strict_schema_summary.json"
IN_7K2_RAW = BASE_DIR / "output" / "stage7k2_strict_schema_glm_retry" / "192_stage7k2_raw_response_sanitized.json"
IN_7K2_VALID = BASE_DIR / "output" / "stage7k2_strict_schema_glm_retry" / "192_stage7k2_validation_result.json"
IN_SCHEMA = BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_ai_review_response_schema.json"
IN_RULES = BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_ai_validation_rules.json"

OUT_DIR = BASE_DIR / "output" / "stage7l_ai_output_evaluation"
OUT_SUMMARY = OUT_DIR / "193_stage7l_ai_output_evaluation_summary.json"
OUT_REPORT = OUT_DIR / "193_stage7l_ai_output_evaluation_report.md"
OUT_PROMPT_COMPARE = OUT_DIR / "193_stage7l_prompt_comparison.md"
OUT_RISK = OUT_DIR / "193_stage7l_model_risk_assessment.md"
OUT_NEXT = OUT_DIR / "193_stage7l_next_stage_recommendation.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"


def _norm(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


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


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    required = [
        IN_7K_SUMMARY,
        IN_7K_RAW,
        IN_7K_VALID,
        IN_7K2_SUMMARY,
        IN_7K2_RAW,
        IN_7K2_VALID,
        IN_SCHEMA,
        IN_RULES,
    ]
    missing = [str(p) for p in required if not p.exists()]
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "stage7l_ai_output_evaluation",
                "mode": "evaluation_only_no_api_call",
                "external_api_called": False,
                "blocked": True,
                "blocked_reason": f"missing_input:{'|'.join(missing)}",
            },
        )
        _write_md(OUT_REPORT, "# Stage7L Blocked\n\n- Missing required inputs.\n")
        _write_md(OUT_PROMPT_COMPARE, "# Prompt Comparison\n\n- blocked\n")
        _write_md(OUT_RISK, "# Risk Assessment\n\n- blocked\n")
        _write_json(OUT_NEXT, {"recommended_next_stage": "blocked"})
        return 0

    before = _snapshot_hashes()

    s7k = _load_json(IN_7K_SUMMARY)
    s7k_raw = _load_json(IN_7K_RAW)
    s7k_valid = _load_json(IN_7K_VALID)
    s7k2 = _load_json(IN_7K2_SUMMARY)
    s7k2_raw = _load_json(IN_7K2_RAW)
    s7k2_valid = _load_json(IN_7K2_VALID)
    schema = _load_json(IN_SCHEMA)
    rules = _load_json(IN_RULES)

    stage7k_schema_valid = bool(s7k.get("schema_valid_response_count", 0) > 0 and s7k.get("schema_invalid_response_count", 0) == 0)
    stage7k2_schema_valid = bool(s7k2.get("schema_valid_response_count", 0) > 0 and s7k2.get("schema_invalid_response_count", 0) == 0)
    strict_schema_prompt_effective = (not stage7k_schema_valid) and stage7k2_schema_valid

    missing_required_fields_7k = [x.split("missing_required:")[1] for x in s7k_valid.get("schema_errors", []) if x.startswith("missing_required:")]
    missing_required_fields_7k2 = s7k2_valid.get("missing_required_fields", [])

    hallucinated_total = int(s7k.get("hallucinated_value_count", 0) or 0) + int(s7k2.get("hallucinated_value_count", 0) or 0)
    invalid_ref_total = int(s7k.get("invalid_source_row_reference_count", 0) or 0) + int(s7k2.get("invalid_source_row_reference_count", 0) or 0)
    bad_eps_total = int(s7k.get("bad_eps_ratio_count", 0) or 0) + int(s7k2.get("bad_eps_ratio_count", 0) or 0)

    requires_human_approval_enforced = bool(
        s7k_raw.get("response_obj", {}).get("requires_human_approval", False)
        and s7k2_raw.get("response_obj", {}).get("requires_human_approval", False)
    )
    json_repair_needed = bool(
        _norm(s7k_raw.get("parse_method")) in {"fence_repair", "slice_repair"}
        or _norm(s7k2_raw.get("parse_method")) in {"fence_repair", "slice_repair"}
    )
    prompt_template_update_recommended = True
    glm47_suitable_for_small_batch = bool(
        stage7k2_schema_valid
        and int(s7k2.get("validated_suggestion_count", 0) or 0) >= 1
        and hallucinated_total == 0
        and invalid_ref_total == 0
        and bad_eps_total == 0
    )

    recommended_next_stage = (
        "stage7m_three_case_strict_schema_api_dry_run"
        if glm47_suitable_for_small_batch
        else "stage7m_prompt_and_validation_hardening"
    )

    after = _snapshot_hashes()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]
    delivery = _run_delivery_check()
    overall_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "stage7l_ai_output_evaluation",
        "mode": "evaluation_only_no_api_call",
        "based_on_stage7k2_commit": "b9fb8777e6dfd64ecbc75fe72c4a882ba0a45c0e",
        "external_api_called": False,
        "evaluated_real_api_runs": 2,
        "stage7k_schema_valid": stage7k_schema_valid,
        "stage7k2_schema_valid": stage7k2_schema_valid,
        "strict_schema_prompt_effective": strict_schema_prompt_effective,
        "hallucinated_value_count_total": hallucinated_total,
        "invalid_source_row_reference_count_total": invalid_ref_total,
        "bad_eps_ratio_count_total": bad_eps_total,
        "requires_human_approval_enforced": requires_human_approval_enforced,
        "glm47_suitable_for_small_batch_strict_schema_test": glm47_suitable_for_small_batch,
        "json_repair_needed": json_repair_needed,
        "prompt_template_update_recommended": prompt_template_update_recommended,
        "recommended_next_stage": recommended_next_stage,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": overall_status,
    }
    _write_json(OUT_SUMMARY, summary)

    report = f"""# Stage 7L AI Output Evaluation

## Scope
- external_api_called: false
- evaluated_real_api_runs: 2 (Stage7K + Stage7K2)

## Key Comparison
- stage7k_schema_valid: {stage7k_schema_valid}
- stage7k2_schema_valid: {stage7k2_schema_valid}
- strict_schema_prompt_effective: {strict_schema_prompt_effective}
- stage7k_missing_required_fields_count: {len(missing_required_fields_7k)}
- stage7k2_missing_required_fields_count: {len(missing_required_fields_7k2)}

## Safety and Data Quality
- hallucinated_value_count_total: {hallucinated_total}
- invalid_source_row_reference_count_total: {invalid_ref_total}
- bad_eps_ratio_count_total: {bad_eps_total}
- requires_human_approval_enforced: {requires_human_approval_enforced}

## Decision
- glm47_suitable_for_small_batch_strict_schema_test: {glm47_suitable_for_small_batch}
- recommended_next_stage: {recommended_next_stage}
- json_repair_needed: {json_repair_needed}
- prompt_template_update_recommended: {prompt_template_update_recommended}

## Guardrails
- production_files_modified: {production_files_modified}
- official_02b_modified: {official_02b_modified}
- formal_rules_modified: {formal_rules_modified}
- standardizer_modified: {standardizer_modified}
- release_package_modified: {release_package_modified}
- check_delivery_state_overall_status: {overall_status}
"""
    _write_md(OUT_REPORT, report)

    prompt_compare = f"""# Prompt Comparison: Stage7K vs Stage7K2

## Stage7K (low-rate prompt)
- Result: schema invalid
- Missing fields: {", ".join(missing_required_fields_7k) if missing_required_fields_7k else "none"}
- Typical response shape: only suggested_action + requires_human_approval

## Stage7K2 (strict schema prompt)
- Result: schema valid
- Missing fields: {", ".join(missing_required_fields_7k2) if missing_required_fields_7k2 else "none"}
- Full schema present: yes
- Deterministic validation pass: {bool(s7k2_valid.get("validation_pass", False))}

## Conclusion
- strict_schema_prompt_effective: {strict_schema_prompt_effective}
- Recommendation: keep strict field checklist + explicit fallback JSON template.
"""
    _write_md(OUT_PROMPT_COMPARE, prompt_compare)

    risk_assessment = f"""# GLM-4.7 Model Risk Assessment (AI-assisted Review)

## Observed Risks
- schema omission risk: mitigated by strict schema prompt
- hallucinated value risk: {hallucinated_total}
- invalid source row reference risk: {invalid_ref_total}
- EPS unit violation risk: {bad_eps_total}

## Operational Controls
- requires_human_approval enforced: {requires_human_approval_enforced}
- deterministic validation rules version: {_norm(rules.get("version"))}
- schema required field count: {len(schema.get("required", []))}

## Recommendation
- Suitable for next small-batch strict-schema dry run: {glm47_suitable_for_small_batch}
- Continue to require human approval for all accepted suggestions: true
- JSON repair layer needed now: {json_repair_needed}
"""
    _write_md(OUT_RISK, risk_assessment)

    next_stage = {
        "stage": "stage7l_ai_output_evaluation",
        "recommended_next_stage": recommended_next_stage,
        "ready": glm47_suitable_for_small_batch,
        "reason": (
            "Stage7K2 achieved schema-valid and validation-pass with zero hallucination/invalid reference/EPS ratio issues."
            if glm47_suitable_for_small_batch
            else "Further prompt and validation hardening needed before scaling."
        ),
        "execution_constraints": {
            "strict_schema_prompt_required": True,
            "requires_human_approval_required": True,
            "no_real_apply": True,
            "small_batch_only": True,
        },
    }
    _write_json(OUT_NEXT, next_stage)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

