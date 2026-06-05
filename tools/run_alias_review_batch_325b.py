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

from datefac.semantic.alias_review_batch_325b import (  # noqa: E402
    DEFAULT_ALIAS_REFINEMENT_DIR,
    DEFAULT_OUTPUT_DIR,
    NOT_READY_DECISION,
    build_alias_review_batch_325b,
    load_alias_review_batch_325b_inputs,
)
from datefac.semantic.alias_review_batch_325b_report import (  # noqa: E402
    alias_review_batch_325b_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "325B",
        "output_dir": str(output_dir),
        "loaded_safe_alias_candidate_count": 0,
        "review_record_count": 0,
        "pending_count": 0,
        "accepted_count": 0,
        "rejected_count": 0,
        "needs_more_info_count": 0,
        "holdout_count": 0,
        "official_assets_modified": False,
        "official_assets_written": [],
        "llm_or_adjudicator_called": False,
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
    write_json(output_dir / "alias_review_batch_325b_summary.json", summary)
    write_json(output_dir / "alias_review_batch_325b_qa.json", qa_json)
    write_json(
        output_dir / "alias_review_batch_325b_review_package.json",
        {"stage": "325B", "decision": NOT_READY_DECISION, "review_records": []},
    )
    write_excel(
        output_dir / "alias_review_batch_325b_workbook.xlsx",
        {
            "summary": pd.DataFrame([summary]),
            "alias_review_records": pd.DataFrame(),
            "review_instructions": pd.DataFrame([{"section": "blocked_input", "instruction": code}]),
            "qa_checks": pd.DataFrame(qa_json["checks"]),
        },
    )
    (output_dir / "alias_review_batch_325b_review_instructions.md").write_text(
        alias_review_batch_325b_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 325B alias review batch prep.")
    parser.add_argument("--alias-refinement-dir", default=str(DEFAULT_ALIAS_REFINEMENT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    alias_refinement_dir = Path(args.alias_refinement_dir)
    output_dir = Path(args.output_dir)

    required_files = [
        (alias_refinement_dir / "alias_candidate_refinement_325a_summary.json", "BLOCKED_MISSING_325A_SUMMARY"),
        (alias_refinement_dir / "alias_candidate_refinement_325a_qa.json", "BLOCKED_MISSING_325A_QA"),
        (alias_refinement_dir / "alias_candidate_refinement_325a_refined_alias_candidates.json", "BLOCKED_MISSING_325A_REFINED_JSON"),
        (alias_refinement_dir / "alias_candidate_refinement_325a_safe_batch.xlsx", "BLOCKED_MISSING_325A_SAFE_BATCH"),
    ]
    for path, code in required_files:
        if not path.exists():
            summary = _blocked_result(output_dir, code)
            print(f"alias_review_batch_325b_summary_json: {output_dir / 'alias_review_batch_325b_summary.json'}")
            print(f"qa_fail_count: {summary.get('qa_fail_count', '')}")
            print(f"decision: {summary.get('decision', '')}")
            return 0

    inputs = load_alias_review_batch_325b_inputs(alias_refinement_dir)
    artifacts = build_alias_review_batch_325b(
        summary_325a=inputs["summary_325a"],
        qa_325a=inputs["qa_325a"],
        refined_json_325a=inputs["refined_json_325a"],
        safe_batch_df=inputs["safe_batch_df"],
        output_dir=output_dir,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = {
        "summary_json": output_dir / "alias_review_batch_325b_summary.json",
        "qa_json": output_dir / "alias_review_batch_325b_qa.json",
        "review_package_json": output_dir / "alias_review_batch_325b_review_package.json",
        "workbook": output_dir / "alias_review_batch_325b_workbook.xlsx",
        "review_instructions_md": output_dir / "alias_review_batch_325b_review_instructions.md",
        "no_apply_proof_json": output_dir / "alias_review_batch_325b_no_apply_proof.json",
    }
    summary = artifacts["summary"]
    write_json(output_files["summary_json"], summary)
    write_json(output_files["qa_json"], artifacts["qa_json"])
    write_json(output_files["review_package_json"], artifacts["review_package_json"])
    write_json(
        output_files["no_apply_proof_json"],
        {
            "stage": "325B",
            "decision": summary["decision"],
            "files_read": [
                str(alias_refinement_dir / "alias_candidate_refinement_325a_summary.json"),
                str(alias_refinement_dir / "alias_candidate_refinement_325a_qa.json"),
                str(alias_refinement_dir / "alias_candidate_refinement_325a_refined_alias_candidates.json"),
                str(alias_refinement_dir / "alias_candidate_refinement_325a_safe_batch.xlsx"),
            ],
            "official_assets_written": [],
            "official_assets_modified": False,
            "llm_or_adjudicator_called": False,
        },
    )
    write_excel(
        output_files["workbook"],
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "alias_review_records": artifacts["review_records_df"],
            "review_instructions": artifacts["instructions_df"],
            "qa_checks": artifacts["qa_checks_df"],
        },
    )
    output_files["review_instructions_md"].write_text(
        alias_review_batch_325b_markdown(summary),
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
    if summary["qa_fail_count"] > 0:
        summary["decision"] = NOT_READY_DECISION
    artifacts["review_package_json"]["decision"] = summary["decision"]

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
    write_json(output_files["review_package_json"], artifacts["review_package_json"])
    write_excel(
        output_files["workbook"],
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "alias_review_records": artifacts["review_records_df"],
            "review_instructions": artifacts["instructions_df"],
            "qa_checks": qa_df.fillna(""),
        },
    )
    output_files["review_instructions_md"].write_text(
        alias_review_batch_325b_markdown(summary),
        encoding="utf-8",
    )

    print(f"alias_review_batch_325b_summary_json: {output_files['summary_json']}")
    print(f"alias_review_batch_325b_qa_json: {output_files['qa_json']}")
    print(f"alias_review_batch_325b_review_package_json: {output_files['review_package_json']}")
    print(f"alias_review_batch_325b_workbook: {output_files['workbook']}")
    print(f"alias_review_batch_325b_review_instructions_md: {output_files['review_instructions_md']}")
    print(f"alias_review_batch_325b_no_apply_proof_json: {output_files['no_apply_proof_json']}")
    for key in [
        "loaded_safe_alias_candidate_count",
        "review_record_count",
        "pending_count",
        "accepted_count",
        "rejected_count",
        "needs_more_info_count",
        "holdout_count",
        "pe_pb_ebit_warning_count",
        "official_assets_modified",
        "llm_or_adjudicator_called",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
