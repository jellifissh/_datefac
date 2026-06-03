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

from datefac.semantic.semantic_adjudication_batch_prep import (
    DEFAULT_CANDIDATE_TEXT_REPAIR_DIR,
    DEFAULT_MAX_ALIAS_BATCH_ITEMS,
    DEFAULT_MAX_SCOPE_BATCH_ITEMS,
    DEFAULT_MAX_TOTAL_BATCH_ITEMS,
    DEFAULT_MINING_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PATCH_APPLICATION_DIR,
    DEFAULT_POST_PATCH_REGRESSION_DIR,
    DEFAULT_TRUST_SPLIT_DIR,
    EXPECTED_323AB_NOT_READY_DECISION,
    build_semantic_adjudication_batch_prep_323ab,
    load_semantic_adjudication_batch_prep_323ab_inputs,
)
from datefac.semantic.semantic_adjudication_batch_prep_report import (
    BATCH_WORKBOOK_SHEET_ORDER,
    HOLDOUT_SHEET_ORDER,
    SIMPLE_ITEM_SHEET_ORDER,
    semantic_adjudication_batch_prep_323ab_review_instructions,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "323A-B",
        "output_dir": str(output_dir),
        "loaded_review_ready_alias_count": 0,
        "loaded_review_ready_scope_count": 0,
        "loaded_holdout_count": 0,
        "selected_alias_batch_count": 0,
        "selected_scope_batch_count": 0,
        "total_batch_count": 0,
        "excluded_review_ready_count": 0,
        "excluded_unit_holdout_count": 0,
        "excluded_ambiguous_holdout_count": 0,
        "excluded_unrepairable_holdout_count": 0,
        "excluded_reason_counts": {},
        "highest_priority_batch_examples": [],
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_323AB_NOT_READY_DECISION,
    }
    qa_json = {
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}],
    }
    batch_json = {"stage": "323A-B", "decision": summary["decision"], "batch_items": []}
    schema_json = {"stage": "323A-B", "schema_status": "BLOCKED_INPUT"}

    workbook_sheets = {
        "summary": pd.DataFrame([summary]),
        "batch_items": pd.DataFrame(),
        "alias_items": pd.DataFrame(),
        "scope_items": pd.DataFrame(),
        "excluded_review_ready_items": pd.DataFrame(),
        "holdout_reference": pd.DataFrame(),
        "qa_summary": pd.DataFrame([{"qa_pass_count": 0, "qa_warn_count": 0, "qa_fail_count": 1, "blocking_reasons": code, "decision": summary["decision"]}]),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
        "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": "Required input directory is missing."}]),
    }
    simple_sheets = {
        "summary": pd.DataFrame([summary]),
        "items": pd.DataFrame(),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
    }
    holdout_sheets = {
        "summary": pd.DataFrame([summary]),
        "excluded_review_ready_items": pd.DataFrame(),
        "holdout_reference": pd.DataFrame(),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
    }

    write_json(output_dir / "semantic_adjudication_batch_prep_323ab_summary.json", summary)
    write_json(output_dir / "semantic_adjudication_batch_prep_323ab_batch.json", batch_json)
    write_json(output_dir / "semantic_adjudication_batch_prep_323ab_schema.json", schema_json)
    write_json(output_dir / "semantic_adjudication_batch_prep_323ab_qa.json", qa_json)
    write_excel(output_dir / "semantic_adjudication_batch_prep_323ab_batch.xlsx", workbook_sheets, BATCH_WORKBOOK_SHEET_ORDER)
    write_excel(output_dir / "semantic_adjudication_batch_prep_323ab_alias_items.xlsx", simple_sheets, SIMPLE_ITEM_SHEET_ORDER)
    write_excel(output_dir / "semantic_adjudication_batch_prep_323ab_scope_items.xlsx", simple_sheets, SIMPLE_ITEM_SHEET_ORDER)
    write_excel(output_dir / "semantic_adjudication_batch_prep_323ab_holdouts.xlsx", holdout_sheets, HOLDOUT_SHEET_ORDER)
    (output_dir / "semantic_adjudication_batch_prep_323ab_review_instructions.md").write_text(
        semantic_adjudication_batch_prep_323ab_review_instructions(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 323A-B semantic adjudication batch prep.")
    parser.add_argument("--candidate-text-repair-dir", default=str(DEFAULT_CANDIDATE_TEXT_REPAIR_DIR))
    parser.add_argument("--mining-dir", default=str(DEFAULT_MINING_DIR))
    parser.add_argument("--patch-application-dir", default=str(DEFAULT_PATCH_APPLICATION_DIR))
    parser.add_argument("--post-patch-regression-dir", default=str(DEFAULT_POST_PATCH_REGRESSION_DIR))
    parser.add_argument("--trust-split-dir", default=str(DEFAULT_TRUST_SPLIT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--max-total-batch-items", type=int, default=DEFAULT_MAX_TOTAL_BATCH_ITEMS)
    parser.add_argument("--max-alias-batch-items", type=int, default=DEFAULT_MAX_ALIAS_BATCH_ITEMS)
    parser.add_argument("--max-scope-batch-items", type=int, default=DEFAULT_MAX_SCOPE_BATCH_ITEMS)
    args = parser.parse_args()

    candidate_text_repair_dir = Path(args.candidate_text_repair_dir)
    mining_dir = Path(args.mining_dir)
    patch_application_dir = Path(args.patch_application_dir)
    post_patch_regression_dir = Path(args.post_patch_regression_dir)
    trust_split_dir = Path(args.trust_split_dir)
    output_dir = Path(args.output_dir)

    required_dirs = [
        (candidate_text_repair_dir, "BLOCKED_MISSING_323AR_DIR"),
        (mining_dir, "BLOCKED_MISSING_323A_MINING_DIR"),
        (patch_application_dir, "BLOCKED_MISSING_322N_PATCH_APPLICATION_DIR"),
        (post_patch_regression_dir, "BLOCKED_MISSING_322O_POST_PATCH_REGRESSION_DIR"),
        (trust_split_dir, "BLOCKED_MISSING_322B2_TRUST_SPLIT_DIR"),
    ]
    for path, code in required_dirs:
        if not path.exists():
            _blocked_result(output_dir, code)
            print(f"semantic_adjudication_batch_prep_323ab_summary_json: {output_dir / 'semantic_adjudication_batch_prep_323ab_summary.json'}")
            return 0

    inputs = load_semantic_adjudication_batch_prep_323ab_inputs(
        candidate_text_repair_dir=candidate_text_repair_dir,
        mining_dir=mining_dir,
        patch_application_dir=patch_application_dir,
        post_patch_regression_dir=post_patch_regression_dir,
        trust_split_dir=trust_split_dir,
    )
    artifacts = build_semantic_adjudication_batch_prep_323ab(
        candidate_text_repair_summary=inputs["candidate_text_repair_summary"],
        candidate_text_repair_qa=inputs["candidate_text_repair_qa"],
        post_patch_summary=inputs["post_patch_summary"],
        review_ready_alias_df=inputs["review_ready_alias_df"],
        review_ready_scope_df=inputs["review_ready_scope_df"],
        holdout_df=inputs["holdout_df"],
        repaired_ranked_df=inputs["repaired_ranked_df"],
        patch_application_log_df=inputs["patch_application_log_df"],
        selected_candidates_df=inputs["selected_candidates_df"],
        mining_summary=inputs["mining_summary"],
        max_total_batch_items=args.max_total_batch_items,
        max_alias_batch_items=args.max_alias_batch_items,
        max_scope_batch_items=args.max_scope_batch_items,
    )

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = output_dir / "semantic_adjudication_batch_prep_323ab_summary.json"
    batch_json_path = output_dir / "semantic_adjudication_batch_prep_323ab_batch.json"
    batch_workbook_path = output_dir / "semantic_adjudication_batch_prep_323ab_batch.xlsx"
    alias_items_path = output_dir / "semantic_adjudication_batch_prep_323ab_alias_items.xlsx"
    scope_items_path = output_dir / "semantic_adjudication_batch_prep_323ab_scope_items.xlsx"
    holdouts_path = output_dir / "semantic_adjudication_batch_prep_323ab_holdouts.xlsx"
    schema_path = output_dir / "semantic_adjudication_batch_prep_323ab_schema.json"
    qa_path = output_dir / "semantic_adjudication_batch_prep_323ab_qa.json"
    review_instructions_path = output_dir / "semantic_adjudication_batch_prep_323ab_review_instructions.md"

    workbook_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "batch_items": artifacts["batch_df"],
        "alias_items": artifacts["alias_items_df"],
        "scope_items": artifacts["scope_items_df"],
        "excluded_review_ready_items": artifacts["excluded_review_ready_df"],
        "holdout_reference": artifacts["holdout_reference_df"],
        "qa_summary": artifacts["qa_summary_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }
    alias_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "items": artifacts["alias_items_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }
    scope_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "items": artifacts["scope_items_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }
    holdout_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "excluded_review_ready_items": artifacts["excluded_review_ready_df"],
        "holdout_reference": artifacts["holdout_reference_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }

    write_json(summary_path, summary)
    write_json(batch_json_path, artifacts["batch_json"])
    write_json(schema_path, artifacts["schema_json"])
    write_json(qa_path, artifacts["qa_json"])
    write_excel(batch_workbook_path, workbook_sheets, BATCH_WORKBOOK_SHEET_ORDER)
    write_excel(alias_items_path, alias_sheets, SIMPLE_ITEM_SHEET_ORDER)
    write_excel(scope_items_path, scope_sheets, SIMPLE_ITEM_SHEET_ORDER)
    write_excel(holdouts_path, holdout_sheets, HOLDOUT_SHEET_ORDER)
    review_instructions_path.write_text(
        semantic_adjudication_batch_prep_323ab_review_instructions(summary),
        encoding="utf-8",
    )

    output_files_written = all(
        path.exists()
        for path in [
            summary_path,
            batch_json_path,
            batch_workbook_path,
            alias_items_path,
            scope_items_path,
            holdouts_path,
            schema_path,
            qa_path,
            review_instructions_path,
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
        "SEMANTIC_ADJUDICATION_BATCH_PREP_323AB_READY_FOR_HUMAN_OR_ADJUDICATOR_REVIEW"
        if summary["qa_fail_count"] == 0
        else EXPECTED_323AB_NOT_READY_DECISION
    )

    workbook_sheets["summary"] = pd.DataFrame([summary]).fillna("")
    workbook_sheets["qa_summary"] = pd.DataFrame(
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
    workbook_sheets["qa_checks"] = qa_df
    alias_sheets["summary"] = pd.DataFrame([summary]).fillna("")
    alias_sheets["qa_checks"] = qa_df
    scope_sheets["summary"] = pd.DataFrame([summary]).fillna("")
    scope_sheets["qa_checks"] = qa_df
    holdout_sheets["summary"] = pd.DataFrame([summary]).fillna("")
    holdout_sheets["qa_checks"] = qa_df

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
    write_excel(batch_workbook_path, workbook_sheets, BATCH_WORKBOOK_SHEET_ORDER)
    write_excel(alias_items_path, alias_sheets, SIMPLE_ITEM_SHEET_ORDER)
    write_excel(scope_items_path, scope_sheets, SIMPLE_ITEM_SHEET_ORDER)
    write_excel(holdouts_path, holdout_sheets, HOLDOUT_SHEET_ORDER)
    review_instructions_path.write_text(
        semantic_adjudication_batch_prep_323ab_review_instructions(summary),
        encoding="utf-8",
    )

    print(f"semantic_adjudication_batch_prep_323ab_summary_json: {summary_path}")
    print(f"semantic_adjudication_batch_prep_323ab_batch_json: {batch_json_path}")
    print(f"semantic_adjudication_batch_prep_323ab_batch_xlsx: {batch_workbook_path}")
    print(f"semantic_adjudication_batch_prep_323ab_alias_items_xlsx: {alias_items_path}")
    print(f"semantic_adjudication_batch_prep_323ab_scope_items_xlsx: {scope_items_path}")
    print(f"semantic_adjudication_batch_prep_323ab_holdouts_xlsx: {holdouts_path}")
    print(f"semantic_adjudication_batch_prep_323ab_schema_json: {schema_path}")
    print(f"semantic_adjudication_batch_prep_323ab_qa_json: {qa_path}")
    print(f"semantic_adjudication_batch_prep_323ab_review_instructions_md: {review_instructions_path}")
    for key in [
        "loaded_review_ready_alias_count",
        "loaded_review_ready_scope_count",
        "selected_alias_batch_count",
        "selected_scope_batch_count",
        "total_batch_count",
        "excluded_review_ready_count",
        "excluded_unit_holdout_count",
        "excluded_ambiguous_holdout_count",
        "excluded_unrepairable_holdout_count",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
