from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.semantic.remaining_burden_planning_323p import (  # noqa: E402
    DEFAULT_CLOSURE_323O_DIR,
    DEFAULT_MINING_323A_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REFERENCE_322O_DIR,
    DEFAULT_REFERENCE_323N_DIR,
    DEFAULT_REPAIR_323AR_DIR,
    DEFAULT_TRUST_SPLIT_322B2_DIR,
    EXPECTED_323P_DECISION,
    EXPECTED_323P_NOT_READY,
    build_remaining_burden_planning_323p,
    load_remaining_burden_planning_323p_inputs,
)
from datefac.semantic.remaining_burden_planning_323p_report import (  # noqa: E402
    remaining_burden_planning_323p_decision_markdown,
    remaining_burden_planning_323p_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "323P",
        "output_dir": str(output_dir),
        "official_rule_count_total": 0,
        "trusted_gain_total": 0,
        "review_reduction_total": 0,
        "remaining_unknown_metric_candidate_count": 0,
        "remaining_unit_unknown_candidate_count": 0,
        "remaining_manual_review_count": 0,
        "historical_duplicate_warning_status": "",
        "alias_candidate_group_count": 0,
        "scope_noise_candidate_group_count": 0,
        "unit_related_holdout_group_count": 0,
        "ambiguous_holdout_group_count": 0,
        "duplicate_cleanup_candidate_count": 0,
        "review_ready_alias_count": 0,
        "review_ready_scope_count": 0,
        "primary_next_cycle_direction": "",
        "secondary_next_cycle_direction": "",
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_323P_NOT_READY,
    }
    qa_json = {
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}],
    }
    decision_json = {
        "decision": EXPECTED_323P_NOT_READY,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "primary_next_cycle_direction": "",
        "secondary_next_cycle_direction": "",
        "do_not_start_next_cycle_yet": True,
    }
    planning_json = {
        "closed_cycle_impact": {},
        "remaining_burden_summary": [],
        "option_comparison": [],
        "recommendations": [],
        "cautions": [],
    }

    write_json(output_dir / "remaining_burden_planning_323p_summary.json", summary)
    write_json(output_dir / "remaining_burden_planning_323p_qa.json", qa_json)
    write_json(output_dir / "remaining_burden_planning_323p_plan.json", planning_json)
    write_excel(
        output_dir / "remaining_burden_planning_323p_summary.xlsx",
        {
            "summary": pd.DataFrame([summary]),
            "closed_cycle_impact": pd.DataFrame(),
            "remaining_burden": pd.DataFrame(),
            "option_comparison": pd.DataFrame(),
            "recommendations": pd.DataFrame(),
            "cautions": pd.DataFrame(),
            "qa_summary": pd.DataFrame(
                [
                    {
                        "qa_pass_count": 0,
                        "qa_warn_count": 0,
                        "qa_fail_count": 1,
                        "blocking_reasons": code,
                        "decision": EXPECTED_323P_NOT_READY,
                    }
                ]
            ),
            "qa_checks": pd.DataFrame(qa_json["checks"]),
            "known_limitations": pd.DataFrame(
                [{"limitation": "blocked_input", "detail": "Required upstream summary is missing."}]
            ),
        },
    )
    (output_dir / "remaining_burden_planning_323p_report.md").write_text(
        remaining_burden_planning_323p_markdown(summary),
        encoding="utf-8",
    )
    (output_dir / "remaining_burden_planning_323p_decision.md").write_text(
        remaining_burden_planning_323p_decision_markdown(decision_json),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 323P remaining burden and next cycle planning.")
    parser.add_argument("--closure-323o-dir", default=str(DEFAULT_CLOSURE_323O_DIR))
    parser.add_argument("--reference-323n-dir", default=str(DEFAULT_REFERENCE_323N_DIR))
    parser.add_argument("--reference-322o-dir", default=str(DEFAULT_REFERENCE_322O_DIR))
    parser.add_argument("--trust-split-322b2-dir", default=str(DEFAULT_TRUST_SPLIT_322B2_DIR))
    parser.add_argument("--mining-323a-dir", default=str(DEFAULT_MINING_323A_DIR))
    parser.add_argument("--repair-323ar-dir", default=str(DEFAULT_REPAIR_323AR_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    closure_323o_dir = Path(args.closure_323o_dir)
    reference_323n_dir = Path(args.reference_323n_dir)
    reference_322o_dir = Path(args.reference_322o_dir)
    trust_split_322b2_dir = Path(args.trust_split_322b2_dir)
    mining_323a_dir = Path(args.mining_323a_dir)
    repair_323ar_dir = Path(args.repair_323ar_dir)
    output_dir = Path(args.output_dir)

    required_files = [
        (closure_323o_dir / "official_semantic_patch_cycle_closure_323o_summary.json", "BLOCKED_MISSING_323O_CLOSURE_SUMMARY"),
        (reference_323n_dir / "post_patch_regression_validation_323n_summary.json", "BLOCKED_MISSING_323N_SUMMARY"),
        (reference_322o_dir / "post_patch_regression_validation_322o_summary.json", "BLOCKED_MISSING_322O_SUMMARY"),
        (trust_split_322b2_dir / "router_mineru_trust_split_322b2_summary.json", "BLOCKED_MISSING_322B2_SUMMARY"),
        (mining_323a_dir / "high_impact_semantic_candidates_mining_323a_summary.json", "BLOCKED_MISSING_323A_SUMMARY"),
        (repair_323ar_dir / "candidate_text_repair_323ar_summary.json", "BLOCKED_MISSING_323AR_SUMMARY"),
    ]
    for path, code in required_files:
        if not path.exists():
            _blocked_result(output_dir, code)
            print(f"remaining_burden_planning_323p_summary_json: {output_dir / 'remaining_burden_planning_323p_summary.json'}")
            return 0

    inputs = load_remaining_burden_planning_323p_inputs(
        closure_323o_dir=closure_323o_dir,
        reference_323n_dir=reference_323n_dir,
        reference_322o_dir=reference_322o_dir,
        trust_split_322b2_dir=trust_split_322b2_dir,
        mining_323a_dir=mining_323a_dir,
        repair_323ar_dir=repair_323ar_dir,
    )
    artifacts = build_remaining_burden_planning_323p(
        closure_323o_summary=inputs["closure_323o_summary"],
        summary_323n=inputs["summary_323n"],
        summary_322o=inputs["summary_322o"],
        summary_322b2=inputs["summary_322b2"],
        summary_323a=inputs["summary_323a"],
        summary_323ar=inputs["summary_323ar"],
        output_dir=output_dir,
    )

    summary = artifacts["summary"]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = {
        "summary_json": output_dir / "remaining_burden_planning_323p_summary.json",
        "qa_json": output_dir / "remaining_burden_planning_323p_qa.json",
        "plan_json": output_dir / "remaining_burden_planning_323p_plan.json",
        "summary_xlsx": output_dir / "remaining_burden_planning_323p_summary.xlsx",
        "report_md": output_dir / "remaining_burden_planning_323p_report.md",
        "decision_md": output_dir / "remaining_burden_planning_323p_decision.md",
    }

    sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "closed_cycle_impact": artifacts["cycle_summary_df"],
        "remaining_burden": artifacts["remaining_burden_df"],
        "option_comparison": artifacts["option_comparison_df"],
        "recommendations": artifacts["recommendation_df"],
        "cautions": artifacts["caution_df"],
        "qa_summary": artifacts["qa_summary_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }

    write_json(output_files["summary_json"], summary)
    write_json(output_files["qa_json"], artifacts["qa_json"])
    write_json(output_files["plan_json"], artifacts["planning_json"])
    write_excel(output_files["summary_xlsx"], sheets)
    output_files["report_md"].write_text(
        remaining_burden_planning_323p_markdown(summary),
        encoding="utf-8",
    )
    output_files["decision_md"].write_text(
        remaining_burden_planning_323p_decision_markdown(artifacts["decision_json"]),
        encoding="utf-8",
    )

    output_files_written = all(path.exists() for path in output_files.values())
    qa_df = artifacts["qa_checks_df"].copy()
    qa_df = pd.concat(
        [
            qa_df,
            pd.DataFrame(
                [
                    {
                        "check_name": "output::artifacts_written_successfully",
                        "status": "PASS" if output_files_written else "FAIL",
                        "detail": str(output_dir),
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    summary["qa_pass_count"] = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    summary["qa_warn_count"] = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    summary["qa_fail_count"] = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    summary["blocking_reasons"] = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []
    summary["decision"] = EXPECTED_323P_DECISION if summary["qa_fail_count"] == 0 else EXPECTED_323P_NOT_READY

    write_json(output_files["summary_json"], summary)
    write_json(
        output_files["qa_json"],
        {
            "qa_pass_count": summary["qa_pass_count"],
            "qa_warn_count": summary["qa_warn_count"],
            "qa_fail_count": summary["qa_fail_count"],
            "blocking_reasons": summary["blocking_reasons"],
            "checks": qa_df.to_dict(orient="records"),
        },
    )
    sheets["summary"] = pd.DataFrame([summary]).fillna("")
    sheets["qa_summary"] = pd.DataFrame(
        [
            {
                "qa_pass_count": summary["qa_pass_count"],
                "qa_warn_count": summary["qa_warn_count"],
                "qa_fail_count": summary["qa_fail_count"],
                "blocking_reasons": " | ".join(summary["blocking_reasons"]),
                "decision": summary["decision"],
            }
        ]
    ).fillna("")
    sheets["qa_checks"] = qa_df
    write_excel(output_files["summary_xlsx"], sheets)
    output_files["report_md"].write_text(
        remaining_burden_planning_323p_markdown(summary),
        encoding="utf-8",
    )
    output_files["decision_md"].write_text(
        remaining_burden_planning_323p_decision_markdown(
            {
                "decision": summary["decision"],
                "qa_fail_count": summary["qa_fail_count"],
                "blocking_reasons": summary["blocking_reasons"],
                "primary_next_cycle_direction": summary["primary_next_cycle_direction"],
                "secondary_next_cycle_direction": summary["secondary_next_cycle_direction"],
                "do_not_start_next_cycle_yet": True,
            }
        ),
        encoding="utf-8",
    )

    print(f"remaining_burden_planning_323p_summary_json: {output_files['summary_json']}")
    print(f"remaining_burden_planning_323p_qa_json: {output_files['qa_json']}")
    print(f"remaining_burden_planning_323p_plan_json: {output_files['plan_json']}")
    print(f"remaining_burden_planning_323p_summary_xlsx: {output_files['summary_xlsx']}")
    print(f"remaining_burden_planning_323p_report_md: {output_files['report_md']}")
    print(f"remaining_burden_planning_323p_decision_md: {output_files['decision_md']}")
    for key in [
        "official_rule_count_total",
        "trusted_gain_total",
        "review_reduction_total",
        "remaining_unknown_metric_candidate_count",
        "remaining_unit_unknown_candidate_count",
        "remaining_manual_review_count",
        "historical_duplicate_warning_status",
        "primary_next_cycle_direction",
        "secondary_next_cycle_direction",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
