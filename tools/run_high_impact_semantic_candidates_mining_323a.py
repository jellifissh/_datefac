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

from datefac.semantic.high_impact_semantic_candidates_mining import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PATCH_APPLICATION_DIR,
    DEFAULT_POST_PATCH_REGRESSION_DIR,
    DEFAULT_TRUST_SPLIT_DIR,
    EXPECTED_323A_NOT_READY_DECISION,
    build_high_impact_semantic_candidates_mining,
    load_high_impact_semantic_candidates_inputs,
)
from datefac.semantic.high_impact_semantic_candidates_report import (
    RANKED_GROUPS_SHEET_ORDER,
    RISK_BUCKET_SHEET_ORDER,
    TOP_OPPORTUNITY_SHEET_ORDER,
    high_impact_semantic_candidates_notes_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "323A",
        "output_dir": str(output_dir),
        "loaded_candidate_count": 0,
        "loaded_unresolved_review_required_candidate_count": 0,
        "closed_rule_count": 0,
        "grouped_candidate_count": 0,
        "alias_opportunity_group_count": 0,
        "scope_noise_group_count": 0,
        "unit_related_group_count": 0,
        "ambiguous_group_count": 0,
        "top_alias_opportunity_count": 0,
        "top_scope_noise_opportunity_count": 0,
        "unit_holdout_count": 0,
        "ambiguous_holdout_count": 0,
        "already_official_redetected_group_count": 0,
        "highest_priority_examples": [],
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_323A_NOT_READY_DECISION,
    }
    qa_json = {
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}],
    }

    ranked_groups_path = output_dir / "high_impact_semantic_candidates_mining_323a_ranked_groups.xlsx"
    alias_path = output_dir / "high_impact_semantic_candidates_mining_323a_top_alias_opportunities.xlsx"
    scope_path = output_dir / "high_impact_semantic_candidates_mining_323a_top_scope_noise_opportunities.xlsx"
    risk_path = output_dir / "high_impact_semantic_candidates_mining_323a_risk_buckets.xlsx"
    summary_path = output_dir / "high_impact_semantic_candidates_mining_323a_summary.json"
    qa_path = output_dir / "high_impact_semantic_candidates_mining_323a_qa.json"
    sampling_path = output_dir / "high_impact_semantic_candidates_mining_323a_sampling_plan.json"
    notes_path = output_dir / "high_impact_semantic_candidates_mining_323a_notes.md"

    ranked_sheets = {
        "summary": pd.DataFrame([summary]),
        "ranked_groups": pd.DataFrame(),
        "closed_rules_reference": pd.DataFrame(),
        "qa_summary": pd.DataFrame([{"qa_pass_count": 0, "qa_warn_count": 0, "qa_fail_count": 1, "blocking_reasons": code, "decision": summary["decision"]}]),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
        "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": "Required input directory is missing."}]),
    }
    top_sheets = {
        "summary": pd.DataFrame([summary]),
        "top_opportunities": pd.DataFrame(),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
    }
    risk_sheets = {
        "summary": pd.DataFrame([summary]),
        "risk_buckets": pd.DataFrame(),
        "unit_holdouts": pd.DataFrame(),
        "ambiguous_holdouts": pd.DataFrame(),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
    }

    write_json(summary_path, summary)
    write_json(qa_path, qa_json)
    write_json(sampling_path, {"stage": "323A", "sampling_plan_record_count": 0, "records": []})
    write_excel(ranked_groups_path, ranked_sheets, RANKED_GROUPS_SHEET_ORDER)
    write_excel(alias_path, top_sheets, TOP_OPPORTUNITY_SHEET_ORDER)
    write_excel(scope_path, top_sheets, TOP_OPPORTUNITY_SHEET_ORDER)
    write_excel(risk_path, risk_sheets, RISK_BUCKET_SHEET_ORDER)
    notes_path.write_text(high_impact_semantic_candidates_notes_markdown(summary), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 323A high-impact semantic candidates mining.")
    parser.add_argument("--post-patch-regression-dir", default=str(DEFAULT_POST_PATCH_REGRESSION_DIR))
    parser.add_argument("--trust-split-dir", default=str(DEFAULT_TRUST_SPLIT_DIR))
    parser.add_argument("--patch-application-dir", default=str(DEFAULT_PATCH_APPLICATION_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    post_patch_regression_dir = Path(args.post_patch_regression_dir)
    trust_split_dir = Path(args.trust_split_dir)
    patch_application_dir = Path(args.patch_application_dir)
    output_dir = Path(args.output_dir)

    required_dirs = [
        (post_patch_regression_dir, "BLOCKED_MISSING_322O_POST_PATCH_REGRESSION_DIR"),
        (trust_split_dir, "BLOCKED_MISSING_322B2_TRUST_SPLIT_DIR"),
        (patch_application_dir, "BLOCKED_MISSING_322N_PATCH_APPLICATION_DIR"),
    ]
    for path, code in required_dirs:
        if not path.exists():
            _blocked_result(output_dir, code)
            print(f"high_impact_semantic_candidates_mining_323a_summary_json: {output_dir / 'high_impact_semantic_candidates_mining_323a_summary.json'}")
            return 0

    inputs = load_high_impact_semantic_candidates_inputs(
        post_patch_regression_dir=post_patch_regression_dir,
        trust_split_dir=trust_split_dir,
        patch_application_dir=patch_application_dir,
    )
    artifacts = build_high_impact_semantic_candidates_mining(
        post_patch_summary=inputs["post_patch_summary"],
        post_patch_qa=inputs["post_patch_qa"],
        trust_summary=inputs["trust_summary"],
        selected_candidates_df=inputs["selected_candidates_df"],
        patch_application_log_df=inputs["patch_application_log_df"],
        output_dir=output_dir,
    )

    summary = artifacts["summary"]
    output_dir.mkdir(parents=True, exist_ok=True)
    ranked_groups_path = output_dir / "high_impact_semantic_candidates_mining_323a_ranked_groups.xlsx"
    alias_path = output_dir / "high_impact_semantic_candidates_mining_323a_top_alias_opportunities.xlsx"
    scope_path = output_dir / "high_impact_semantic_candidates_mining_323a_top_scope_noise_opportunities.xlsx"
    risk_path = output_dir / "high_impact_semantic_candidates_mining_323a_risk_buckets.xlsx"
    summary_path = output_dir / "high_impact_semantic_candidates_mining_323a_summary.json"
    qa_path = output_dir / "high_impact_semantic_candidates_mining_323a_qa.json"
    sampling_path = output_dir / "high_impact_semantic_candidates_mining_323a_sampling_plan.json"
    notes_path = output_dir / "high_impact_semantic_candidates_mining_323a_notes.md"

    ranked_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "ranked_groups": artifacts["grouped_df"],
        "closed_rules_reference": artifacts["closed_rule_df"],
        "qa_summary": artifacts["qa_summary_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }
    alias_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "top_opportunities": artifacts["alias_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }
    scope_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "top_opportunities": artifacts["scope_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }
    risk_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "risk_buckets": artifacts["risk_bucket_df"],
        "unit_holdouts": artifacts["unit_holdout_df"],
        "ambiguous_holdouts": artifacts["ambiguous_holdout_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }

    write_json(summary_path, summary)
    write_json(qa_path, artifacts["qa_json"])
    write_json(sampling_path, artifacts["sampling_plan_json"])
    write_excel(ranked_groups_path, ranked_sheets, RANKED_GROUPS_SHEET_ORDER)
    write_excel(alias_path, alias_sheets, TOP_OPPORTUNITY_SHEET_ORDER)
    write_excel(scope_path, scope_sheets, TOP_OPPORTUNITY_SHEET_ORDER)
    write_excel(risk_path, risk_sheets, RISK_BUCKET_SHEET_ORDER)
    notes_path.write_text(high_impact_semantic_candidates_notes_markdown(summary), encoding="utf-8")

    output_files_written = all(
        path.exists()
        for path in [
            ranked_groups_path,
            alias_path,
            scope_path,
            risk_path,
            summary_path,
            qa_path,
            sampling_path,
            notes_path,
        ]
    )
    qa_df = artifacts["qa_checks_df"].copy()
    qa_df = pd.concat(
        [
            qa_df,
            pd.DataFrame(
                [
                    {
                        "check_name": "output_files_written_successfully",
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
    summary["decision"] = (
        "HIGH_IMPACT_SEMANTIC_CANDIDATES_323A_READY_FOR_323B_OR_323A_ADJUDICATION_BATCH_PREP"
        if summary["qa_fail_count"] == 0
        else EXPECTED_323A_NOT_READY_DECISION
    )

    ranked_sheets["summary"] = pd.DataFrame([summary]).fillna("")
    ranked_sheets["qa_summary"] = pd.DataFrame(
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
    ranked_sheets["qa_checks"] = qa_df
    alias_sheets["summary"] = pd.DataFrame([summary]).fillna("")
    alias_sheets["qa_checks"] = qa_df
    scope_sheets["summary"] = pd.DataFrame([summary]).fillna("")
    scope_sheets["qa_checks"] = qa_df
    risk_sheets["summary"] = pd.DataFrame([summary]).fillna("")
    risk_sheets["qa_checks"] = qa_df

    write_json(summary_path, summary)
    write_json(
        qa_path,
        {
            "qa_pass_count": summary["qa_pass_count"],
            "qa_warn_count": summary["qa_warn_count"],
            "qa_fail_count": summary["qa_fail_count"],
            "blocking_reasons": summary["blocking_reasons"],
            "checks": qa_df.to_dict(orient="records"),
        },
    )
    write_excel(ranked_groups_path, ranked_sheets, RANKED_GROUPS_SHEET_ORDER)
    write_excel(alias_path, alias_sheets, TOP_OPPORTUNITY_SHEET_ORDER)
    write_excel(scope_path, scope_sheets, TOP_OPPORTUNITY_SHEET_ORDER)
    write_excel(risk_path, risk_sheets, RISK_BUCKET_SHEET_ORDER)
    notes_path.write_text(high_impact_semantic_candidates_notes_markdown(summary), encoding="utf-8")

    print(f"high_impact_semantic_candidates_mining_323a_summary_json: {summary_path}")
    print(f"high_impact_semantic_candidates_mining_323a_ranked_groups_xlsx: {ranked_groups_path}")
    print(f"high_impact_semantic_candidates_mining_323a_top_alias_opportunities_xlsx: {alias_path}")
    print(f"high_impact_semantic_candidates_mining_323a_top_scope_noise_opportunities_xlsx: {scope_path}")
    print(f"high_impact_semantic_candidates_mining_323a_risk_buckets_xlsx: {risk_path}")
    print(f"high_impact_semantic_candidates_mining_323a_sampling_plan_json: {sampling_path}")
    print(f"high_impact_semantic_candidates_mining_323a_qa_json: {qa_path}")
    print(f"high_impact_semantic_candidates_mining_323a_notes_md: {notes_path}")
    for key in [
        "loaded_unresolved_review_required_candidate_count",
        "grouped_candidate_count",
        "top_alias_opportunity_count",
        "top_scope_noise_opportunity_count",
        "unit_holdout_count",
        "ambiguous_holdout_count",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
