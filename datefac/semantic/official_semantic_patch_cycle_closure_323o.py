from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


EXPECTED_322O_DECISION = "POST_PATCH_REGRESSION_VALIDATION_322O_READY_TO_CLOSE_OFFICIAL_PATCH_CYCLE"
EXPECTED_322N_DECISION = "OFFICIAL_SEMANTIC_PATCH_APPLICATION_322N_READY_FOR_322O_POST_PATCH_REGRESSION"
EXPECTED_323M_DECISION = "OFFICIAL_PATCH_APPLICATION_323M_READY_FOR_323N_POST_PATCH_REGRESSION"
EXPECTED_323N_READY_DECISION = "POST_PATCH_REGRESSION_VALIDATION_323N_READY_TO_CLOSE_OFFICIAL_PATCH_CYCLE"
EXPECTED_323N_READY_WITH_WARNINGS_DECISION = "POST_PATCH_REGRESSION_VALIDATION_323N_READY_WITH_WARNINGS"
EXPECTED_323O_READY_DECISION = "OFFICIAL_SEMANTIC_PATCH_CYCLE_323O_CLOSED_READY_FOR_NEXT_CYCLE_PLANNING"
EXPECTED_323O_NOT_READY_DECISION = "OFFICIAL_SEMANTIC_PATCH_CYCLE_323O_NOT_READY_FOR_CLOSURE"

DEFAULT_REFERENCE_322O_DIR = Path(r"D:\_datefac\output\post_patch_regression_validation_322o")
DEFAULT_REFERENCE_322N_DIR = Path(r"D:\_datefac\output\official_semantic_patch_application_322n")
DEFAULT_REFERENCE_323N_DIR = Path(r"D:\_datefac\output\post_patch_regression_validation_323n")
DEFAULT_REFERENCE_323M_DIR = Path(r"D:\_datefac\output\official_patch_application_323m")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\official_semantic_patch_cycle_closure_323o")

EXPECTED_COUNTS = {
    "rules_322": 10,
    "trusted_gain_322": 49,
    "review_reduction_322": 287,
    "rules_323": 6,
    "trusted_gain_323": 44,
    "review_reduction_323": 129,
    "combined_rules": 16,
    "combined_trusted_gain": 93,
    "combined_review_reduction": 416,
}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _safe_int(value: Any) -> int:
    if value in ("", None):
        return 0
    try:
        if isinstance(value, bool):
            return int(value)
        return int(float(value))
    except Exception:
        return 0


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def load_official_semantic_patch_cycle_closure_323o_inputs(
    reference_322o_dir: Path,
    reference_322n_dir: Path,
    reference_323n_dir: Path,
    reference_323m_dir: Path,
) -> Dict[str, Any]:
    return {
        "summary_322o": _read_json(
            reference_322o_dir / "post_patch_regression_validation_322o_summary.json"
        ),
        "summary_322n": _read_json(
            reference_322n_dir / "official_semantic_patch_application_322n_summary.json"
        ),
        "summary_323n": _read_json(
            reference_323n_dir / "post_patch_regression_validation_323n_summary.json"
        ),
        "summary_323m": _read_json(
            reference_323m_dir / "official_patch_application_323m_summary.json"
        ),
        "qa_323n": _read_json(reference_323n_dir / "post_patch_regression_validation_323n_qa.json"),
    }


def build_official_semantic_patch_cycle_closure_323o(
    summary_322o: Dict[str, Any],
    summary_322n: Dict[str, Any],
    summary_323n: Dict[str, Any],
    summary_323m: Dict[str, Any],
    qa_323n: Dict[str, Any],
    output_dir: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa(
        "readiness::322o_decision",
        "PASS" if _norm(summary_322o.get("decision")) == EXPECTED_322O_DECISION else "FAIL",
        _norm(summary_322o.get("decision")),
    )
    add_qa(
        "readiness::322o_qa_fail_count",
        "PASS" if _safe_int(summary_322o.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_322o.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::322n_decision",
        "PASS" if _norm(summary_322n.get("decision")) == EXPECTED_322N_DECISION else "FAIL",
        _norm(summary_322n.get("decision")),
    )
    add_qa(
        "readiness::322n_qa_fail_count",
        "PASS" if _safe_int(summary_322n.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_322n.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::323m_decision",
        "PASS" if _norm(summary_323m.get("decision")) == EXPECTED_323M_DECISION else "FAIL",
        _norm(summary_323m.get("decision")),
    )
    add_qa(
        "readiness::323m_qa_fail_count",
        "PASS" if _safe_int(summary_323m.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_323m.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::323n_decision",
        "PASS"
        if _norm(summary_323n.get("decision")) in {EXPECTED_323N_READY_DECISION, EXPECTED_323N_READY_WITH_WARNINGS_DECISION}
        else "FAIL",
        _norm(summary_323n.get("decision")),
    )
    add_qa(
        "readiness::323n_qa_fail_count",
        "PASS" if _safe_int(summary_323n.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_323n.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::323n_warning_shape",
        "PASS"
        if (
            _safe_int(summary_323n.get("qa_warn_count")) == 0
            or (
                _safe_int(summary_323n.get("qa_warn_count")) == 1
                and any(
                    _norm(check.get("check_name")) == "duplicates::historical_duplicates_unchanged"
                    and _norm(check.get("status")) == "WARN"
                    for check in qa_323n.get("checks", [])
                )
            )
        )
        else "FAIL",
        f"qa_warn_count={summary_323n.get('qa_warn_count', '')}",
    )

    rules_322 = _safe_int(summary_322o.get("official_rule_visibility_total"))
    trusted_gain_322 = _safe_int(summary_322o.get("trusted_gain_322o"))
    review_reduction_322 = _safe_int(summary_322o.get("review_reduction_322o"))
    out_of_scope_gain_322 = _safe_int(summary_322o.get("out_of_scope_or_rejected_gain_322o"))

    rules_323 = _safe_int(summary_323n.get("official_rule_visibility_total"))
    trusted_gain_323 = _safe_int(summary_323n.get("trusted_gain_323n"))
    review_reduction_323 = _safe_int(summary_323n.get("review_reduction_323n"))
    out_of_scope_gain_323 = _safe_int(summary_323n.get("out_of_scope_or_rejected_gain_323n"))

    combined_rules = rules_322 + rules_323
    combined_trusted_gain = trusted_gain_322 + trusted_gain_323
    combined_review_reduction = review_reduction_322 + review_reduction_323
    combined_out_of_scope_gain = out_of_scope_gain_322 + out_of_scope_gain_323

    add_qa(
        "cycle_summary::rules_322",
        "PASS" if rules_322 == EXPECTED_COUNTS["rules_322"] else "FAIL",
        f"expected={EXPECTED_COUNTS['rules_322']} actual={rules_322}",
    )
    add_qa(
        "cycle_summary::trusted_gain_322",
        "PASS" if trusted_gain_322 == EXPECTED_COUNTS["trusted_gain_322"] else "FAIL",
        f"expected={EXPECTED_COUNTS['trusted_gain_322']} actual={trusted_gain_322}",
    )
    add_qa(
        "cycle_summary::review_reduction_322",
        "PASS" if review_reduction_322 == EXPECTED_COUNTS["review_reduction_322"] else "FAIL",
        f"expected={EXPECTED_COUNTS['review_reduction_322']} actual={review_reduction_322}",
    )
    add_qa(
        "cycle_summary::rules_323",
        "PASS" if rules_323 == EXPECTED_COUNTS["rules_323"] else "FAIL",
        f"expected={EXPECTED_COUNTS['rules_323']} actual={rules_323}",
    )
    add_qa(
        "cycle_summary::trusted_gain_323",
        "PASS" if trusted_gain_323 == EXPECTED_COUNTS["trusted_gain_323"] else "FAIL",
        f"expected={EXPECTED_COUNTS['trusted_gain_323']} actual={trusted_gain_323}",
    )
    add_qa(
        "cycle_summary::review_reduction_323",
        "PASS" if review_reduction_323 == EXPECTED_COUNTS["review_reduction_323"] else "FAIL",
        f"expected={EXPECTED_COUNTS['review_reduction_323']} actual={review_reduction_323}",
    )
    add_qa(
        "cycle_summary::combined_rules",
        "PASS" if combined_rules == EXPECTED_COUNTS["combined_rules"] else "FAIL",
        f"expected={EXPECTED_COUNTS['combined_rules']} actual={combined_rules}",
    )
    add_qa(
        "cycle_summary::combined_trusted_gain",
        "PASS" if combined_trusted_gain == EXPECTED_COUNTS["combined_trusted_gain"] else "FAIL",
        f"expected={EXPECTED_COUNTS['combined_trusted_gain']} actual={combined_trusted_gain}",
    )
    add_qa(
        "cycle_summary::combined_review_reduction",
        "PASS" if combined_review_reduction == EXPECTED_COUNTS["combined_review_reduction"] else "FAIL",
        f"expected={EXPECTED_COUNTS['combined_review_reduction']} actual={combined_review_reduction}",
    )

    warnings_323 = []
    if _safe_int(summary_323n.get("qa_warn_count")) > 0:
        warnings_323.append("historical duplicates unchanged only")
    remaining_risks = [
        "historical duplicate entries remain in official assets but 323M introduced no new duplicate delta",
        "remaining unresolved semantic candidates still require next-cycle mining and adjudication prep",
    ]
    recommendations = [
        "start next cycle from remaining unresolved and review-required semantic opportunities rather than broad new patch application",
        "preserve duplicate-safe validation gates so historical duplicate warnings stay non-blocking only when delta remains zero",
        "continue using cached replay before any future official promotion to validate trusted gain and review reduction exactly",
    ]

    cycle_summary_df = pd.DataFrame(
        [
            {
                "cycle": "322",
                "official_rule_count": rules_322,
                "trusted_gain": trusted_gain_322,
                "review_reduction": review_reduction_322,
                "out_of_scope_or_rejected_gain": out_of_scope_gain_322,
                "decision": _norm(summary_322o.get("decision")),
                "warnings": "",
            },
            {
                "cycle": "323",
                "official_rule_count": rules_323,
                "trusted_gain": trusted_gain_323,
                "review_reduction": review_reduction_323,
                "out_of_scope_or_rejected_gain": out_of_scope_gain_323,
                "decision": _norm(summary_323n.get("decision")),
                "warnings": " | ".join(warnings_323),
            },
            {
                "cycle": "combined",
                "official_rule_count": combined_rules,
                "trusted_gain": combined_trusted_gain,
                "review_reduction": combined_review_reduction,
                "out_of_scope_or_rejected_gain": combined_out_of_scope_gain,
                "decision": EXPECTED_323O_READY_DECISION,
                "warnings": " | ".join(warnings_323),
            },
        ]
    ).fillna("")

    stage_alignment_df = pd.DataFrame(
        [
            {
                "stage": "322N",
                "decision": _norm(summary_322n.get("decision")),
                "qa_fail_count": _safe_int(summary_322n.get("qa_fail_count")),
                "rule_count": _safe_int(summary_322n.get("approved_patch_count")),
                "trusted_gain": _safe_int(summary_322n.get("expected_trusted_gain")),
                "review_reduction": _safe_int(summary_322n.get("expected_review_reduction")),
            },
            {
                "stage": "322O",
                "decision": _norm(summary_322o.get("decision")),
                "qa_fail_count": _safe_int(summary_322o.get("qa_fail_count")),
                "rule_count": _safe_int(summary_322o.get("official_rule_visibility_total")),
                "trusted_gain": _safe_int(summary_322o.get("trusted_gain_322o")),
                "review_reduction": _safe_int(summary_322o.get("review_reduction_322o")),
            },
            {
                "stage": "323M",
                "decision": _norm(summary_323m.get("decision")),
                "qa_fail_count": _safe_int(summary_323m.get("qa_fail_count")),
                "rule_count": _safe_int(summary_323m.get("approved_patch_count")),
                "trusted_gain": _safe_int(summary_323m.get("expected_trusted_gain")),
                "review_reduction": _safe_int(summary_323m.get("expected_review_reduction")),
            },
            {
                "stage": "323N",
                "decision": _norm(summary_323n.get("decision")),
                "qa_fail_count": _safe_int(summary_323n.get("qa_fail_count")),
                "rule_count": _safe_int(summary_323n.get("official_rule_visibility_total")),
                "trusted_gain": _safe_int(summary_323n.get("trusted_gain_323n")),
                "review_reduction": _safe_int(summary_323n.get("review_reduction_323n")),
            },
        ]
    ).fillna("")

    warning_rows = [{"cycle": "323", "warning": item} for item in warnings_323] or [{"cycle": "323", "warning": ""}]
    risk_rows = [{"risk": item} for item in remaining_risks]
    recommendation_rows = [{"recommendation": item} for item in recommendations]

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    summary = {
        "stage": "323O",
        "output_dir": str(output_dir),
        "rules_322": rules_322,
        "trusted_gain_322": trusted_gain_322,
        "review_reduction_322": review_reduction_322,
        "out_of_scope_or_rejected_gain_322": out_of_scope_gain_322,
        "rules_323": rules_323,
        "trusted_gain_323": trusted_gain_323,
        "review_reduction_323": review_reduction_323,
        "out_of_scope_or_rejected_gain_323": out_of_scope_gain_323,
        "combined_rules": combined_rules,
        "combined_trusted_gain": combined_trusted_gain,
        "combined_review_reduction": combined_review_reduction,
        "combined_out_of_scope_or_rejected_gain": combined_out_of_scope_gain,
        "warning_323": "historical duplicates unchanged only" if warnings_323 else "",
        "remaining_risk_count": len(remaining_risks),
        "next_cycle_recommendation_count": len(recommendations),
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": EXPECTED_323O_READY_DECISION if qa_fail_count == 0 else EXPECTED_323O_NOT_READY_DECISION,
    }

    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }
    decision_json = {
        "decision": summary["decision"],
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "warning_323": summary["warning_323"],
        "next_step": (
            "Proceed to next-cycle planning using remaining unresolved and warning-aware semantic opportunity mining."
            if qa_fail_count == 0
            else "Review blocking reasons before declaring the cycle closed."
        ),
    }
    closure_json = {
        "cycle_322": cycle_summary_df.iloc[0].to_dict(),
        "cycle_323": cycle_summary_df.iloc[1].to_dict(),
        "combined": cycle_summary_df.iloc[2].to_dict(),
        "remaining_risks": remaining_risks,
        "next_cycle_recommendations": recommendations,
    }

    qa_summary_df = pd.DataFrame(
        [
            {
                "qa_pass_count": qa_pass_count,
                "qa_warn_count": qa_warn_count,
                "qa_fail_count": qa_fail_count,
                "blocking_reasons": " | ".join(blocking_reasons),
                "decision": summary["decision"],
            }
        ]
    ).fillna("")

    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "summary_only",
                "detail": "323O aggregates existing stage summaries only and does not rerun patch application or regression replay.",
            },
            {
                "limitation": "no_asset_or_pipeline_modification",
                "detail": "323O does not modify official semantic assets, production pipeline code, or cached stage artifacts.",
            },
        ]
    ).fillna("")

    return {
        "summary": summary,
        "qa_json": qa_json,
        "decision_json": decision_json,
        "closure_json": closure_json,
        "cycle_summary_df": cycle_summary_df,
        "stage_alignment_df": stage_alignment_df,
        "warning_df": pd.DataFrame(warning_rows).fillna(""),
        "remaining_risks_df": pd.DataFrame(risk_rows).fillna(""),
        "recommendations_df": pd.DataFrame(recommendation_rows).fillna(""),
        "qa_checks_df": qa_df,
        "qa_summary_df": qa_summary_df,
        "known_limitations_df": known_limitations_df,
    }
