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

from datefac.semantic.alias_candidate_refinement_325a import (  # noqa: E402
    DEFAULT_CANDIDATE_TEXT_REPAIR_DIR,
    DEFAULT_CYCLE_CLOSURE_DIR,
    DEFAULT_HIGH_IMPACT_MINING_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_POST_PATCH_323N_DIR,
    DEFAULT_POST_PATCH_324M_DIR,
    DEFAULT_PREVIOUS_BATCH_PREP_DIR,
    DEFAULT_PREVIOUS_SANITY_GATE_DIR,
    DEFAULT_REMAINING_BURDEN_DIR,
    DEFAULT_TRUST_SPLIT_DIR,
    FORMAL_SCOPE_RULES_PATH,
    MAX_SAFE_BATCH_COUNT,
    NOT_READY_DECISION,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_alias_candidate_refinement_325a,
    load_alias_candidate_refinement_325a_inputs,
)
from datefac.semantic.alias_candidate_refinement_325a_report import (  # noqa: E402
    alias_candidate_refinement_325a_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "325A",
        "output_dir": str(output_dir),
        "input_alias_inventory_count": 0,
        "safe_alias_review_batch_count": 0,
        "holdout_count": 0,
        "risk_bucket_counts": {},
        "official_assets_modified": False,
        "official_assets_written": [],
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": NOT_READY_DECISION,
    }
    qa_json = {
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}],
    }
    write_json(output_dir / "alias_candidate_refinement_325a_summary.json", summary)
    write_json(output_dir / "alias_candidate_refinement_325a_qa.json", qa_json)
    write_json(
        output_dir / "alias_candidate_refinement_325a_refined_alias_candidates.json",
        {"stage": "325A", "decision": NOT_READY_DECISION, "safe_alias_review_batch": [], "holdout_candidates": []},
    )
    write_json(
        output_dir / "alias_candidate_refinement_325a_no_apply_proof.json",
        {"stage": "325A", "official_assets_written": [], "official_assets_modified": False},
    )
    sheets = {
        "summary": pd.DataFrame([summary]),
        "refined_alias_candidates": pd.DataFrame(),
        "safe_batch": pd.DataFrame(),
        "holdout_candidates": pd.DataFrame(),
        "already_official_overlap": pd.DataFrame(),
        "risk_bucket_summary": pd.DataFrame(),
        "qa_summary": pd.DataFrame(
            [{"qa_pass_count": 0, "qa_warn_count": 0, "qa_fail_count": 1, "blocking_reasons": code, "decision": NOT_READY_DECISION}]
        ),
        "qa_checks": pd.DataFrame(qa_json["checks"]),
        "notes": pd.DataFrame([{"note_type": "blocked_input", "detail": code}]),
    }
    write_excel(output_dir / "alias_candidate_refinement_325a_refined_alias_candidates.xlsx", sheets)
    (output_dir / "alias_candidate_refinement_325a_notes.md").write_text(
        alias_candidate_refinement_325a_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 325A alias candidate refinement.")
    parser.add_argument("--remaining-burden-dir", default=str(DEFAULT_REMAINING_BURDEN_DIR))
    parser.add_argument("--candidate-text-repair-dir", default=str(DEFAULT_CANDIDATE_TEXT_REPAIR_DIR))
    parser.add_argument("--high-impact-mining-dir", default=str(DEFAULT_HIGH_IMPACT_MINING_DIR))
    parser.add_argument("--previous-batch-prep-dir", default=str(DEFAULT_PREVIOUS_BATCH_PREP_DIR))
    parser.add_argument("--previous-sanity-gate-dir", default=str(DEFAULT_PREVIOUS_SANITY_GATE_DIR))
    parser.add_argument("--cycle-closure-dir", default=str(DEFAULT_CYCLE_CLOSURE_DIR))
    parser.add_argument("--post-patch-324m-dir", default=str(DEFAULT_POST_PATCH_324M_DIR))
    parser.add_argument("--post-patch-323n-dir", default=str(DEFAULT_POST_PATCH_323N_DIR))
    parser.add_argument("--trust-split-dir", default=str(DEFAULT_TRUST_SPLIT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--max-safe-batch-count", type=int, default=MAX_SAFE_BATCH_COUNT)
    args = parser.parse_args()

    remaining_burden_dir = Path(args.remaining_burden_dir)
    candidate_text_repair_dir = Path(args.candidate_text_repair_dir)
    high_impact_mining_dir = Path(args.high_impact_mining_dir)
    previous_batch_prep_dir = Path(args.previous_batch_prep_dir)
    previous_sanity_gate_dir = Path(args.previous_sanity_gate_dir)
    cycle_closure_dir = Path(args.cycle_closure_dir)
    post_patch_324m_dir = Path(args.post_patch_324m_dir)
    post_patch_323n_dir = Path(args.post_patch_323n_dir)
    trust_split_dir = Path(args.trust_split_dir)
    output_dir = Path(args.output_dir)

    required_files = [
        (remaining_burden_dir / "remaining_burden_planning_323p_summary.json", "BLOCKED_MISSING_323P_SUMMARY"),
        (candidate_text_repair_dir / "candidate_text_repair_323ar_summary.json", "BLOCKED_MISSING_323AR_SUMMARY"),
        (candidate_text_repair_dir / "candidate_text_repair_323ar_review_ready_package.xlsx", "BLOCKED_MISSING_323AR_REVIEW_READY_WORKBOOK"),
        (high_impact_mining_dir / "high_impact_semantic_candidates_mining_323a_summary.json", "BLOCKED_MISSING_323A_SUMMARY"),
        (high_impact_mining_dir / "high_impact_semantic_candidates_mining_323a_top_alias_opportunities.xlsx", "BLOCKED_MISSING_323A_TOP_ALIAS_WORKBOOK"),
        (previous_batch_prep_dir / "semantic_adjudication_batch_prep_323ab_summary.json", "BLOCKED_MISSING_323AB_SUMMARY"),
        (previous_batch_prep_dir / "semantic_adjudication_batch_prep_323ab_alias_items.xlsx", "BLOCKED_MISSING_323AB_ALIAS_ITEMS"),
        (previous_sanity_gate_dir / "adjudication_batch_sanity_gate_323c_summary.json", "BLOCKED_MISSING_323C_SUMMARY"),
        (previous_sanity_gate_dir / "adjudication_batch_sanity_gate_323c_gated_batch.xlsx", "BLOCKED_MISSING_323C_GATED_BATCH"),
        (cycle_closure_dir / "official_scope_patch_cycle_closure_324n_summary.json", "BLOCKED_MISSING_324N_SUMMARY"),
        (post_patch_324m_dir / "post_patch_regression_validation_324m_summary.json", "BLOCKED_MISSING_324M_SUMMARY"),
        (post_patch_323n_dir / "post_patch_regression_validation_323n_summary.json", "BLOCKED_MISSING_323N_SUMMARY"),
        (trust_split_dir / "router_mineru_trust_split_322b2_summary.json", "BLOCKED_MISSING_322B2_TRUST_SPLIT_SUMMARY"),
        (SEMANTIC_ALIAS_ASSET_PATH, "BLOCKED_MISSING_OFFICIAL_ALIAS_ASSET"),
        (FORMAL_SCOPE_RULES_PATH, "BLOCKED_MISSING_OFFICIAL_SCOPE_ASSET"),
    ]
    for path, code in required_files:
        if not path.exists():
            summary = _blocked_result(output_dir, code)
            print(f"alias_candidate_refinement_325a_summary_json: {output_dir / 'alias_candidate_refinement_325a_summary.json'}")
            print(f"qa_fail_count: {summary.get('qa_fail_count', '')}")
            print(f"decision: {summary.get('decision', '')}")
            return 0

    inputs = load_alias_candidate_refinement_325a_inputs(
        remaining_burden_dir=remaining_burden_dir,
        candidate_text_repair_dir=candidate_text_repair_dir,
        high_impact_mining_dir=high_impact_mining_dir,
        previous_batch_prep_dir=previous_batch_prep_dir,
        previous_sanity_gate_dir=previous_sanity_gate_dir,
        cycle_closure_dir=cycle_closure_dir,
        post_patch_324m_dir=post_patch_324m_dir,
        post_patch_323n_dir=post_patch_323n_dir,
        trust_split_dir=trust_split_dir,
    )
    artifacts = build_alias_candidate_refinement_325a(
        summary_323p=inputs["summary_323p"],
        summary_323ar=inputs["summary_323ar"],
        summary_323a=inputs["summary_323a"],
        summary_323ab=inputs["summary_323ab"],
        summary_323c=inputs["summary_323c"],
        summary_324n=inputs["summary_324n"],
        summary_324m=inputs["summary_324m"],
        summary_323n=inputs["summary_323n"],
        trust_summary=inputs["trust_summary"],
        review_ready_alias_df=inputs["review_ready_alias_df"],
        top_alias_df=inputs["top_alias_df"],
        previous_alias_items_df=inputs["previous_alias_items_df"],
        sanity_lookup=inputs["sanity_lookup"],
        alias_asset=inputs["alias_asset"],
        scope_asset=inputs["scope_asset"],
        output_dir=output_dir,
        max_safe_batch_count=args.max_safe_batch_count,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = {
        "summary_json": output_dir / "alias_candidate_refinement_325a_summary.json",
        "qa_json": output_dir / "alias_candidate_refinement_325a_qa.json",
        "refined_json": output_dir / "alias_candidate_refinement_325a_refined_alias_candidates.json",
        "refined_xlsx": output_dir / "alias_candidate_refinement_325a_refined_alias_candidates.xlsx",
        "safe_batch_xlsx": output_dir / "alias_candidate_refinement_325a_safe_batch.xlsx",
        "holdout_xlsx": output_dir / "alias_candidate_refinement_325a_holdout_candidates.xlsx",
        "overlap_xlsx": output_dir / "alias_candidate_refinement_325a_already_official_overlap.xlsx",
        "risk_summary_xlsx": output_dir / "alias_candidate_refinement_325a_risk_bucket_summary.xlsx",
        "notes_md": output_dir / "alias_candidate_refinement_325a_notes.md",
        "no_apply_proof_json": output_dir / "alias_candidate_refinement_325a_no_apply_proof.json",
    }
    summary = artifacts["summary"]
    sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "refined_alias_candidates": artifacts["refined_alias_candidates_df"],
        "safe_batch": artifacts["safe_batch_df"],
        "holdout_candidates": artifacts["holdout_df"],
        "already_official_overlap": artifacts["overlap_df"],
        "risk_bucket_summary": artifacts["risk_summary_df"],
        "qa_summary": artifacts["qa_summary_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "notes": artifacts["notes_df"],
    }
    write_json(output_files["summary_json"], summary)
    write_json(output_files["qa_json"], artifacts["qa_json"])
    write_json(output_files["refined_json"], artifacts["refined_json"])
    write_json(output_files["no_apply_proof_json"], artifacts["no_apply_proof_json"])
    write_excel(output_files["refined_xlsx"], sheets)
    write_excel(output_files["safe_batch_xlsx"], {"safe_batch": artifacts["safe_batch_df"], "qa_checks": artifacts["qa_checks_df"]})
    write_excel(output_files["holdout_xlsx"], {"holdout_candidates": artifacts["holdout_df"], "qa_checks": artifacts["qa_checks_df"]})
    write_excel(output_files["overlap_xlsx"], {"already_official_overlap": artifacts["overlap_df"], "qa_checks": artifacts["qa_checks_df"]})
    write_excel(output_files["risk_summary_xlsx"], {"risk_bucket_summary": artifacts["risk_summary_df"], "qa_checks": artifacts["qa_checks_df"]})
    output_files["notes_md"].write_text(alias_candidate_refinement_325a_markdown(summary), encoding="utf-8")

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
    if summary["qa_fail_count"] > 0:
        summary["decision"] = NOT_READY_DECISION

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
    output_files["notes_md"].write_text(alias_candidate_refinement_325a_markdown(summary), encoding="utf-8")

    print(f"alias_candidate_refinement_325a_summary_json: {output_files['summary_json']}")
    print(f"alias_candidate_refinement_325a_qa_json: {output_files['qa_json']}")
    print(f"alias_candidate_refinement_325a_refined_json: {output_files['refined_json']}")
    print(f"alias_candidate_refinement_325a_refined_xlsx: {output_files['refined_xlsx']}")
    print(f"alias_candidate_refinement_325a_safe_batch_xlsx: {output_files['safe_batch_xlsx']}")
    print(f"alias_candidate_refinement_325a_holdout_xlsx: {output_files['holdout_xlsx']}")
    print(f"alias_candidate_refinement_325a_overlap_xlsx: {output_files['overlap_xlsx']}")
    print(f"alias_candidate_refinement_325a_risk_summary_xlsx: {output_files['risk_summary_xlsx']}")
    print(f"alias_candidate_refinement_325a_notes_md: {output_files['notes_md']}")
    print(f"alias_candidate_refinement_325a_no_apply_proof_json: {output_files['no_apply_proof_json']}")
    for key in [
        "input_alias_inventory_count",
        "excluded_already_official_count",
        "excluded_category_mismatch_count",
        "excluded_scope_noise_or_disclosure_text_count",
        "excluded_unit_related_count",
        "excluded_generic_ambiguous_label_count",
        "excluded_weak_evidence_count",
        "excluded_duplicate_or_conflict_count",
        "safe_alias_review_batch_count",
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
