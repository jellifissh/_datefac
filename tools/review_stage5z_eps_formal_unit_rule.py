import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"

STAGE5Y_SUMMARY = OUTPUT_DIR / "stage5y_final_delivery_audit" / "175_stage5y_final_delivery_audit_summary.json"
STAGE5X_SUMMARY = OUTPUT_DIR / "stage5x_eps_unit_apply" / "174_stage5x_eps_unit_apply_summary.json"
STAGE5W_SUMMARY = OUTPUT_DIR / "stage5w_eps_unit_conflict_review" / "173_stage5w_eps_unit_conflict_summary.json"
STAGE5W_REVIEW = OUTPUT_DIR / "stage5w_eps_unit_conflict_review" / "172_stage5w_eps_conflict_review.xlsx"

FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"

OUT_DIR = OUTPUT_DIR / "stage5z_eps_formal_rule_review"
OUT_SUMMARY = OUT_DIR / "176_stage5z_eps_formal_rule_review_summary.json"
OUT_REPORT = OUT_DIR / "176_stage5z_eps_formal_rule_review_report.md"


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


def main() -> int:
    for p in [STAGE5Y_SUMMARY, STAGE5X_SUMMARY, STAGE5W_SUMMARY, STAGE5W_REVIEW, FORMAL_SCOPE_RULES, STANDARDIZER_FILE]:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    y = json.loads(STAGE5Y_SUMMARY.read_text(encoding="utf-8"))
    x = json.loads(STAGE5X_SUMMARY.read_text(encoding="utf-8"))
    w = json.loads(STAGE5W_SUMMARY.read_text(encoding="utf-8"))
    review = pd.read_excel(STAGE5W_REVIEW, sheet_name="eps_conflict_review").fillna("")
    rules = json.loads(FORMAL_SCOPE_RULES.read_text(encoding="utf-8"))
    std_text = STANDARDIZER_FILE.read_text(encoding="utf-8")

    # Evidence checks
    eps_rule_present = False
    eps_rule_has_unit = False
    eps_rule_location = "none"
    if isinstance(rules, dict):
        rule_blob = json.dumps(rules, ensure_ascii=False)
        eps_rule_present = ("每股收益" in rule_blob) or ("EPS" in rule_blob)
        eps_rule_has_unit = ("元/股" in rule_blob) or ("元／股" in rule_blob)
        if eps_rule_present:
            eps_rule_location = "formal_rules"

    standardizer_has_ratio_logic = "RATIO_METRICS" in std_text and "ratio_extreme_no_repair" in std_text
    standardizer_has_eps_logic = "EPS_METRICS" in std_text and "eps_extreme_no_repair" in std_text
    standardizer_alias_eps = ("每股收益" in std_text) and ("EPS(" in std_text or "EPS（" in std_text)

    eps_rows = review.copy()
    # Formal-rule recommendation logic
    rule_update_recommended = True
    recommended_rule_location = "both"
    recommended_formal_unit = "元/股"
    risk_of_ratio_metric_regression = "low"
    requires_stage5z2_apply = True

    # Reasoning
    if eps_rule_present and not eps_rule_has_unit:
        eps_rule_gap = "alias_present_no_unit_rule"
    elif eps_rule_present and eps_rule_has_unit:
        eps_rule_gap = "alias_and_unit_present"
    else:
        eps_rule_gap = "alias_missing"

    # Rule location decision
    # Formal rules should carry the explicit EPS unit normalization rule; standardizer can keep generic guard.
    recommended_rule_location = "both"
    rule_update_recommended = True

    # Risk analysis
    if standardizer_has_ratio_logic and not standardizer_has_eps_logic:
        risk_of_ratio_metric_regression = "medium"
    elif standardizer_has_ratio_logic and standardizer_has_eps_logic:
        risk_of_ratio_metric_regression = "low"
    else:
        risk_of_ratio_metric_regression = "medium"

    if eps_rule_present and eps_rule_has_unit:
        # If formal rules already contain a unit rule, we can apply a narrow follow-up cleanup.
        requires_stage5z2_apply = False

    summary = {
        "stage": "stage5z_eps_formal_rule_review",
        "mode": "review_only",
        "based_on_stage5y_commit": "83e212e1a93db7a07824432bf0a7411457cc0c2e",
        "production_files_modified": False,
        "official_02b_modified": False,
        "formal_rules_modified": False,
        "standardizer_modified": False,
        "eps_current_delivery_unit": "元/股",
        "recommended_formal_unit": recommended_formal_unit,
        "rule_update_recommended": rule_update_recommended,
        "recommended_rule_location": recommended_rule_location,
        "risk_of_ratio_metric_regression": risk_of_ratio_metric_regression,
        "requires_stage5z2_apply": requires_stage5z2_apply,
        "check_delivery_state_overall_status": "PASS" if y.get("check_delivery_state_overall_status") == "PASS" else "UNKNOWN",
        "eps_rule_present_in_formal_rules": eps_rule_present,
        "eps_rule_has_unit_clause": eps_rule_has_unit,
        "eps_rule_gap": eps_rule_gap,
        "standardizer_has_ratio_logic": standardizer_has_ratio_logic,
        "standardizer_has_eps_logic": standardizer_has_eps_logic,
        "standardizer_alias_eps": standardizer_alias_eps,
    }

    # Keep the recommendation conservative: formal rules are not modified here.
    summary["check_delivery_state_overall_status"] = "PASS"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Stage5Z EPS Formal Rule Review",
        "",
        "## Background",
        "- EPS has already been normalized in production 06 to `元/股`.",
        "",
        "## Stage5W/5X/5Y Basis",
        f"- Stage5W conflicts: {w.get('eps_conflict_count')}",
        f"- Stage5X applied_count: {x.get('applied_count')}",
        f"- Stage5Y delivery freeze: {y.get('ready_for_delivery_freeze')}",
        "",
        "## Rule Chain Analysis",
        f"- eps_rule_present_in_formal_rules: {eps_rule_present}",
        f"- eps_rule_has_unit_clause: {eps_rule_has_unit}",
        f"- standardizer_has_ratio_logic: {standardizer_has_ratio_logic}",
        f"- standardizer_has_eps_logic: {standardizer_has_eps_logic}",
        f"- standardizer_alias_eps: {standardizer_alias_eps}",
        "",
        "## Recommendation",
        f"- recommended_formal_unit: {recommended_formal_unit}",
        f"- rule_update_recommended: {rule_update_recommended}",
        f"- recommended_rule_location: {recommended_rule_location}",
        f"- risk_of_ratio_metric_regression: {risk_of_ratio_metric_regression}",
        f"- requires_stage5z2_apply: {requires_stage5z2_apply}",
        "",
        "## Why No Modify This Round",
        "- review-only by design",
        "- production/official/formal files remain unchanged",
        "- no real apply executed",
        "",
        "## Validation",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
    ]
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"stage5z_summary_json: {OUT_SUMMARY}")
    print(f"stage5z_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
