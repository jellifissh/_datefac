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

from datefac.semantic.scope_noise_refinement_324a import (  # noqa: E402
    DEFAULT_ALIAS_RULES_PATH,
    DEFAULT_MINING_323A_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PLANNING_323P_DIR,
    DEFAULT_POST_PATCH_323N_DIR,
    DEFAULT_REPAIR_323AR_DIR,
    DEFAULT_SCOPE_RULES_PATH,
    EXPECTED_324A_DECISION,
    EXPECTED_324A_NOT_READY,
    build_scope_noise_refinement_324a,
    load_scope_noise_refinement_324a_inputs,
)
from datefac.semantic.scope_noise_refinement_324a_report import (  # noqa: E402
    scope_noise_refinement_324a_decision_markdown,
    scope_noise_refinement_324a_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "324A",
        "output_dir": str(output_dir),
        "input_scope_group_count": 0,
        "review_ready_scope_group_count_323ar": 0,
        "excluded_already_official_count": 0,
        "excluded_323m_scope_rule_count": 0,
        "excluded_duplicate_accounted_count": 0,
        "excluded_unrepairable_holdout_count": 0,
        "refined_scope_candidate_count": 0,
        "holdout_count": 0,
        "top_examples": [],
        "excluded_reason_counts": {},
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_324A_NOT_READY,
    }
    qa_json = {
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}],
    }
    batch_json = {
        "stage": "324A",
        "decision": EXPECTED_324A_NOT_READY,
        "refined_scope_candidates": [],
        "excluded_source_groups": [],
        "duplicate_provenance": [],
    }

    write_json(output_dir / "scope_noise_refinement_324a_summary.json", summary)
    write_json(output_dir / "scope_noise_refinement_324a_qa.json", qa_json)
    write_json(output_dir / "scope_noise_refinement_324a_refined_batch.json", batch_json)
    write_excel(
        output_dir / "scope_noise_refinement_324a_scope_review_batch.xlsx",
        {
            "summary": pd.DataFrame([summary]),
            "refined_scope_candidates": pd.DataFrame(),
            "excluded_source_groups": pd.DataFrame(),
            "excluded_reason_summary": pd.DataFrame(),
            "duplicate_provenance": pd.DataFrame(),
            "review_instructions": pd.DataFrame(
                [{"instruction_type": "blocked_input", "detail": "Required upstream artifact is missing."}]
            ),
            "qa_summary": pd.DataFrame(
                [
                    {
                        "qa_pass_count": 0,
                        "qa_warn_count": 0,
                        "qa_fail_count": 1,
                        "blocking_reasons": code,
                        "decision": EXPECTED_324A_NOT_READY,
                    }
                ]
            ),
            "qa_checks": pd.DataFrame(qa_json["checks"]),
            "known_limitations": pd.DataFrame(
                [{"limitation": "blocked_input", "detail": "Required upstream artifact is missing."}]
            ),
        },
    )
    (output_dir / "scope_noise_refinement_324a_report.md").write_text(
        scope_noise_refinement_324a_markdown(summary),
        encoding="utf-8",
    )
    (output_dir / "scope_noise_refinement_324a_decision.md").write_text(
        scope_noise_refinement_324a_decision_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 324A scope noise candidate refinement / batch prep.")
    parser.add_argument("--planning-323p-dir", default=str(DEFAULT_PLANNING_323P_DIR))
    parser.add_argument("--mining-323a-dir", default=str(DEFAULT_MINING_323A_DIR))
    parser.add_argument("--repair-323ar-dir", default=str(DEFAULT_REPAIR_323AR_DIR))
    parser.add_argument("--post-patch-323n-dir", default=str(DEFAULT_POST_PATCH_323N_DIR))
    parser.add_argument("--scope-rules-path", default=str(DEFAULT_SCOPE_RULES_PATH))
    parser.add_argument("--alias-rules-path", default=str(DEFAULT_ALIAS_RULES_PATH))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    planning_323p_dir = Path(args.planning_323p_dir)
    mining_323a_dir = Path(args.mining_323a_dir)
    repair_323ar_dir = Path(args.repair_323ar_dir)
    post_patch_323n_dir = Path(args.post_patch_323n_dir)
    scope_rules_path = Path(args.scope_rules_path)
    alias_rules_path = Path(args.alias_rules_path)
    output_dir = Path(args.output_dir)

    required_files = [
        (planning_323p_dir / "remaining_burden_planning_323p_summary.json", "BLOCKED_MISSING_323P_SUMMARY"),
        (mining_323a_dir / "high_impact_semantic_candidates_mining_323a_summary.json", "BLOCKED_MISSING_323A_SUMMARY"),
        (
            mining_323a_dir / "high_impact_semantic_candidates_mining_323a_top_scope_noise_opportunities.xlsx",
            "BLOCKED_MISSING_323A_TOP_SCOPE_WORKBOOK",
        ),
        (mining_323a_dir / "high_impact_semantic_candidates_mining_323a_sampling_plan.json", "BLOCKED_MISSING_323A_SAMPLING_PLAN"),
        (repair_323ar_dir / "candidate_text_repair_323ar_summary.json", "BLOCKED_MISSING_323AR_SUMMARY"),
        (repair_323ar_dir / "candidate_text_repair_323ar_review_ready_package.xlsx", "BLOCKED_MISSING_323AR_REVIEW_READY_WORKBOOK"),
        (repair_323ar_dir / "candidate_text_repair_323ar_repaired_ranked_groups.xlsx", "BLOCKED_MISSING_323AR_REPAIRED_RANKED_WORKBOOK"),
        (post_patch_323n_dir / "post_patch_regression_validation_323n_summary.json", "BLOCKED_MISSING_323N_SUMMARY"),
        (scope_rules_path, "BLOCKED_MISSING_SCOPE_RULES"),
        (alias_rules_path, "BLOCKED_MISSING_ALIAS_RULES"),
    ]
    for path, code in required_files:
        if not path.exists():
            _blocked_result(output_dir, code)
            print(f"scope_noise_refinement_324a_summary_json: {output_dir / 'scope_noise_refinement_324a_summary.json'}")
            return 0

    inputs = load_scope_noise_refinement_324a_inputs(
        planning_323p_dir=planning_323p_dir,
        mining_323a_dir=mining_323a_dir,
        repair_323ar_dir=repair_323ar_dir,
        post_patch_323n_dir=post_patch_323n_dir,
        scope_rules_path=scope_rules_path,
        alias_rules_path=alias_rules_path,
    )
    artifacts = build_scope_noise_refinement_324a(
        summary_323p=inputs["summary_323p"],
        summary_323a=inputs["summary_323a"],
        summary_323ar=inputs["summary_323ar"],
        summary_323n=inputs["summary_323n"],
        top_scope_df=inputs["top_scope_df"],
        review_ready_scope_df=inputs["review_ready_scope_df"],
        repaired_ranked_scope_df=inputs["repaired_ranked_scope_df"],
        sampling_scope_df=inputs["sampling_scope_df"],
        scope_rules_json=inputs["scope_rules_json"],
        alias_rules_json=inputs["alias_rules_json"],
        output_dir=output_dir,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = {
        "summary_json": output_dir / "scope_noise_refinement_324a_summary.json",
        "qa_json": output_dir / "scope_noise_refinement_324a_qa.json",
        "refined_batch_json": output_dir / "scope_noise_refinement_324a_refined_batch.json",
        "scope_review_batch_xlsx": output_dir / "scope_noise_refinement_324a_scope_review_batch.xlsx",
        "report_md": output_dir / "scope_noise_refinement_324a_report.md",
        "decision_md": output_dir / "scope_noise_refinement_324a_decision.md",
    }

    summary = artifacts["summary"]
    qa_json = artifacts["qa_json"]
    sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "refined_scope_candidates": artifacts["refined_scope_candidates_df"],
        "excluded_source_groups": artifacts["excluded_source_groups_df"],
        "excluded_reason_summary": artifacts["excluded_reason_summary_df"],
        "duplicate_provenance": artifacts["duplicate_provenance_df"],
        "review_instructions": artifacts["review_instruction_df"],
        "qa_summary": artifacts["qa_summary_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }

    write_json(output_files["summary_json"], summary)
    write_json(output_files["qa_json"], qa_json)
    write_json(output_files["refined_batch_json"], artifacts["refined_batch_json"])
    write_excel(output_files["scope_review_batch_xlsx"], sheets)
    output_files["report_md"].write_text(
        scope_noise_refinement_324a_markdown(summary),
        encoding="utf-8",
    )
    output_files["decision_md"].write_text(
        scope_noise_refinement_324a_decision_markdown(summary),
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
    summary["blocking_reasons"] = (
        qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []
    )
    summary["decision"] = EXPECTED_324A_DECISION if summary["qa_fail_count"] == 0 else EXPECTED_324A_NOT_READY

    qa_json = {
        "qa_pass_count": summary["qa_pass_count"],
        "qa_warn_count": summary["qa_warn_count"],
        "qa_fail_count": summary["qa_fail_count"],
        "blocking_reasons": summary["blocking_reasons"],
        "checks": qa_df.to_dict(orient="records"),
    }
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
    sheets["qa_checks"] = qa_df.fillna("")
    artifacts["refined_batch_json"]["decision"] = summary["decision"]

    write_json(output_files["summary_json"], summary)
    write_json(output_files["qa_json"], qa_json)
    write_json(output_files["refined_batch_json"], artifacts["refined_batch_json"])
    write_excel(output_files["scope_review_batch_xlsx"], sheets)
    output_files["report_md"].write_text(
        scope_noise_refinement_324a_markdown(summary),
        encoding="utf-8",
    )
    output_files["decision_md"].write_text(
        scope_noise_refinement_324a_decision_markdown(summary),
        encoding="utf-8",
    )

    print(f"scope_noise_refinement_324a_summary_json: {output_files['summary_json']}")
    print(f"scope_noise_refinement_324a_qa_json: {output_files['qa_json']}")
    print(f"scope_noise_refinement_324a_refined_batch_json: {output_files['refined_batch_json']}")
    print(f"scope_noise_refinement_324a_scope_review_batch_xlsx: {output_files['scope_review_batch_xlsx']}")
    print(f"scope_noise_refinement_324a_report_md: {output_files['report_md']}")
    print(f"scope_noise_refinement_324a_decision_md: {output_files['decision_md']}")
    for key in [
        "input_scope_group_count",
        "excluded_already_official_count",
        "refined_scope_candidate_count",
        "holdout_count",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
