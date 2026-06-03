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

from datefac.semantic.candidate_text_repair import (
    DEFAULT_MINING_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_POST_PATCH_REGRESSION_DIR,
    DEFAULT_TRUST_SPLIT_DIR,
    EXPECTED_323AR_NOT_READY_DECISION,
    build_candidate_text_repair_323ar,
    load_candidate_text_repair_inputs,
)
from datefac.semantic.candidate_text_repair_report import (
    REPAIRED_RANKED_GROUPS_SHEET_ORDER,
    REPAIRED_TOP_PACKAGE_SHEET_ORDER,
    REVIEW_READY_PACKAGE_SHEET_ORDER,
    candidate_text_repair_323ar_notes_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "323A-R",
        "output_dir": str(output_dir),
        "input_323a_decision": "",
        "input_323a_qa_fail_count": 1,
        "grouped_candidate_count_323a": 0,
        "mojibake_group_count": 0,
        "mojibake_top_alias_count": 0,
        "mojibake_top_scope_count": 0,
        "mojibake_sample_text_count": 0,
        "deterministic_repair_count": 0,
        "already_clean_count": 0,
        "unrepairable_holdout_count": 0,
        "review_ready_alias_count": 0,
        "review_ready_scope_count": 0,
        "review_ready_total_count": 0,
        "highest_priority_repaired_examples": [],
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_323AR_NOT_READY_DECISION,
    }
    qa_json = {
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}],
    }

    repaired_ranked_sheets = {
        "summary": pd.DataFrame([summary]),
        "repaired_ranked_groups": pd.DataFrame(),
        "mojibake_groups": pd.DataFrame(),
        "unrepairable_holdouts": pd.DataFrame(),
        "qa_summary": pd.DataFrame([{"qa_pass_count": 0, "qa_warn_count": 0, "qa_fail_count": 1, "blocking_reasons": code, "decision": summary["decision"]}]),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
        "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": "Required input directory is missing."}]),
    }
    top_package_sheets = {
        "summary": pd.DataFrame([summary]),
        "repaired_top_opportunities": pd.DataFrame(),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
    }
    review_ready_sheets = {
        "summary": pd.DataFrame([summary]),
        "review_ready_alias": pd.DataFrame(),
        "review_ready_scope_noise": pd.DataFrame(),
        "holdout_groups": pd.DataFrame(),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
        "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": "Required input directory is missing."}]),
    }

    write_json(output_dir / "candidate_text_repair_323ar_summary.json", summary)
    write_json(output_dir / "candidate_text_repair_323ar_qa.json", qa_json)
    write_excel(
        output_dir / "candidate_text_repair_323ar_repaired_ranked_groups.xlsx",
        repaired_ranked_sheets,
        REPAIRED_RANKED_GROUPS_SHEET_ORDER,
    )
    write_excel(
        output_dir / "candidate_text_repair_323ar_repaired_top_alias_opportunities.xlsx",
        top_package_sheets,
        REPAIRED_TOP_PACKAGE_SHEET_ORDER,
    )
    write_excel(
        output_dir / "candidate_text_repair_323ar_repaired_top_scope_noise_opportunities.xlsx",
        top_package_sheets,
        REPAIRED_TOP_PACKAGE_SHEET_ORDER,
    )
    write_excel(
        output_dir / "candidate_text_repair_323ar_mojibake_groups.xlsx",
        repaired_ranked_sheets,
        REPAIRED_RANKED_GROUPS_SHEET_ORDER,
    )
    write_excel(
        output_dir / "candidate_text_repair_323ar_unrepairable_holdouts.xlsx",
        repaired_ranked_sheets,
        REPAIRED_RANKED_GROUPS_SHEET_ORDER,
    )
    write_excel(
        output_dir / "candidate_text_repair_323ar_review_ready_package.xlsx",
        review_ready_sheets,
        REVIEW_READY_PACKAGE_SHEET_ORDER,
    )
    (output_dir / "candidate_text_repair_323ar_notes.md").write_text(
        candidate_text_repair_323ar_notes_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 323A-R candidate text repair and review readiness.")
    parser.add_argument("--mining-dir", default=str(DEFAULT_MINING_DIR))
    parser.add_argument("--trust-split-dir", default=str(DEFAULT_TRUST_SPLIT_DIR))
    parser.add_argument("--post-patch-regression-dir", default=str(DEFAULT_POST_PATCH_REGRESSION_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    mining_dir = Path(args.mining_dir)
    trust_split_dir = Path(args.trust_split_dir)
    post_patch_regression_dir = Path(args.post_patch_regression_dir)
    output_dir = Path(args.output_dir)

    required_dirs = [
        (mining_dir, "BLOCKED_MISSING_323A_MINING_DIR"),
        (trust_split_dir, "BLOCKED_MISSING_322B2_TRUST_SPLIT_DIR"),
        (post_patch_regression_dir, "BLOCKED_MISSING_322O_POST_PATCH_REGRESSION_DIR"),
    ]
    for path, code in required_dirs:
        if not path.exists():
            _blocked_result(output_dir, code)
            print(f"candidate_text_repair_323ar_summary_json: {output_dir / 'candidate_text_repair_323ar_summary.json'}")
            return 0

    inputs = load_candidate_text_repair_inputs(
        mining_dir=mining_dir,
        trust_split_dir=trust_split_dir,
        post_patch_regression_dir=post_patch_regression_dir,
    )
    artifacts = build_candidate_text_repair_323ar(
        mining_summary=inputs["mining_summary"],
        mining_qa=inputs["mining_qa"],
        post_patch_summary=inputs["post_patch_summary"],
        ranked_groups_df=inputs["ranked_groups_df"],
        top_alias_df=inputs["top_alias_df"],
        top_scope_df=inputs["top_scope_df"],
        selected_candidates_df=inputs["selected_candidates_df"],
    )

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = output_dir / "candidate_text_repair_323ar_summary.json"
    qa_path = output_dir / "candidate_text_repair_323ar_qa.json"
    repaired_ranked_groups_path = output_dir / "candidate_text_repair_323ar_repaired_ranked_groups.xlsx"
    repaired_top_alias_path = output_dir / "candidate_text_repair_323ar_repaired_top_alias_opportunities.xlsx"
    repaired_top_scope_path = output_dir / "candidate_text_repair_323ar_repaired_top_scope_noise_opportunities.xlsx"
    mojibake_groups_path = output_dir / "candidate_text_repair_323ar_mojibake_groups.xlsx"
    unrepairable_holdouts_path = output_dir / "candidate_text_repair_323ar_unrepairable_holdouts.xlsx"
    review_ready_package_path = output_dir / "candidate_text_repair_323ar_review_ready_package.xlsx"
    notes_path = output_dir / "candidate_text_repair_323ar_notes.md"

    repaired_ranked_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "repaired_ranked_groups": artifacts["repaired_df"],
        "mojibake_groups": artifacts["mojibake_groups_df"],
        "unrepairable_holdouts": artifacts["unrepairable_df"],
        "qa_summary": artifacts["qa_summary_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }
    alias_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "repaired_top_opportunities": artifacts["review_ready_alias_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }
    scope_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "repaired_top_opportunities": artifacts["review_ready_scope_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }
    review_ready_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "review_ready_alias": artifacts["review_ready_alias_df"],
        "review_ready_scope_noise": artifacts["review_ready_scope_df"],
        "holdout_groups": artifacts["holdout_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }

    write_json(summary_path, summary)
    write_json(qa_path, artifacts["qa_json"])
    write_excel(repaired_ranked_groups_path, repaired_ranked_sheets, REPAIRED_RANKED_GROUPS_SHEET_ORDER)
    write_excel(repaired_top_alias_path, alias_sheets, REPAIRED_TOP_PACKAGE_SHEET_ORDER)
    write_excel(repaired_top_scope_path, scope_sheets, REPAIRED_TOP_PACKAGE_SHEET_ORDER)
    write_excel(mojibake_groups_path, repaired_ranked_sheets, REPAIRED_RANKED_GROUPS_SHEET_ORDER)
    write_excel(unrepairable_holdouts_path, repaired_ranked_sheets, REPAIRED_RANKED_GROUPS_SHEET_ORDER)
    write_excel(review_ready_package_path, review_ready_sheets, REVIEW_READY_PACKAGE_SHEET_ORDER)
    notes_path.write_text(candidate_text_repair_323ar_notes_markdown(summary), encoding="utf-8")

    output_files_written = all(
        path.exists()
        for path in [
            summary_path,
            qa_path,
            repaired_ranked_groups_path,
            repaired_top_alias_path,
            repaired_top_scope_path,
            mojibake_groups_path,
            unrepairable_holdouts_path,
            review_ready_package_path,
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
        "CANDIDATE_TEXT_REPAIR_323AR_READY_FOR_ADJUDICATION_BATCH_PREP"
        if summary["qa_fail_count"] == 0
        else EXPECTED_323AR_NOT_READY_DECISION
    )

    repaired_ranked_sheets["summary"] = pd.DataFrame([summary]).fillna("")
    repaired_ranked_sheets["qa_summary"] = pd.DataFrame(
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
    repaired_ranked_sheets["qa_checks"] = qa_df
    alias_sheets["summary"] = pd.DataFrame([summary]).fillna("")
    alias_sheets["qa_checks"] = qa_df
    scope_sheets["summary"] = pd.DataFrame([summary]).fillna("")
    scope_sheets["qa_checks"] = qa_df
    review_ready_sheets["summary"] = pd.DataFrame([summary]).fillna("")
    review_ready_sheets["qa_checks"] = qa_df

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
    write_excel(repaired_ranked_groups_path, repaired_ranked_sheets, REPAIRED_RANKED_GROUPS_SHEET_ORDER)
    write_excel(repaired_top_alias_path, alias_sheets, REPAIRED_TOP_PACKAGE_SHEET_ORDER)
    write_excel(repaired_top_scope_path, scope_sheets, REPAIRED_TOP_PACKAGE_SHEET_ORDER)
    write_excel(mojibake_groups_path, repaired_ranked_sheets, REPAIRED_RANKED_GROUPS_SHEET_ORDER)
    write_excel(unrepairable_holdouts_path, repaired_ranked_sheets, REPAIRED_RANKED_GROUPS_SHEET_ORDER)
    write_excel(review_ready_package_path, review_ready_sheets, REVIEW_READY_PACKAGE_SHEET_ORDER)
    notes_path.write_text(candidate_text_repair_323ar_notes_markdown(summary), encoding="utf-8")

    print(f"candidate_text_repair_323ar_summary_json: {summary_path}")
    print(f"candidate_text_repair_323ar_qa_json: {qa_path}")
    print(f"candidate_text_repair_323ar_repaired_ranked_groups_xlsx: {repaired_ranked_groups_path}")
    print(f"candidate_text_repair_323ar_repaired_top_alias_opportunities_xlsx: {repaired_top_alias_path}")
    print(f"candidate_text_repair_323ar_repaired_top_scope_noise_opportunities_xlsx: {repaired_top_scope_path}")
    print(f"candidate_text_repair_323ar_mojibake_groups_xlsx: {mojibake_groups_path}")
    print(f"candidate_text_repair_323ar_unrepairable_holdouts_xlsx: {unrepairable_holdouts_path}")
    print(f"candidate_text_repair_323ar_review_ready_package_xlsx: {review_ready_package_path}")
    print(f"candidate_text_repair_323ar_notes_md: {notes_path}")
    for key in [
        "mojibake_group_count",
        "mojibake_top_alias_count",
        "mojibake_top_scope_count",
        "mojibake_sample_text_count",
        "deterministic_repair_count",
        "already_clean_count",
        "unrepairable_holdout_count",
        "review_ready_alias_count",
        "review_ready_scope_count",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
