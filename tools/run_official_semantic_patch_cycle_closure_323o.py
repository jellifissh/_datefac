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

from datefac.semantic.official_semantic_patch_cycle_closure_323o import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REFERENCE_322N_DIR,
    DEFAULT_REFERENCE_322O_DIR,
    DEFAULT_REFERENCE_323M_DIR,
    DEFAULT_REFERENCE_323N_DIR,
    EXPECTED_323O_NOT_READY_DECISION,
    EXPECTED_323O_READY_DECISION,
    build_official_semantic_patch_cycle_closure_323o,
    load_official_semantic_patch_cycle_closure_323o_inputs,
)
from datefac.semantic.official_semantic_patch_cycle_closure_323o_report import (  # noqa: E402
    official_semantic_patch_cycle_closure_323o_decision_markdown,
    official_semantic_patch_cycle_closure_323o_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "323O",
        "output_dir": str(output_dir),
        "rules_322": 0,
        "trusted_gain_322": 0,
        "review_reduction_322": 0,
        "out_of_scope_or_rejected_gain_322": 0,
        "rules_323": 0,
        "trusted_gain_323": 0,
        "review_reduction_323": 0,
        "out_of_scope_or_rejected_gain_323": 0,
        "combined_rules": 0,
        "combined_trusted_gain": 0,
        "combined_review_reduction": 0,
        "combined_out_of_scope_or_rejected_gain": 0,
        "warning_323": "",
        "remaining_risk_count": 0,
        "next_cycle_recommendation_count": 0,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_323O_NOT_READY_DECISION,
    }
    qa_json = {
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}],
    }
    decision_json = {
        "decision": EXPECTED_323O_NOT_READY_DECISION,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "warning_323": "",
        "next_step": "Load all required upstream summaries before closing the cycle.",
    }
    closure_json = {
        "cycle_322": {},
        "cycle_323": {},
        "combined": {},
        "remaining_risks": [],
        "next_cycle_recommendations": [],
    }

    write_json(output_dir / "official_semantic_patch_cycle_closure_323o_summary.json", summary)
    write_json(output_dir / "official_semantic_patch_cycle_closure_323o_qa.json", qa_json)
    write_json(output_dir / "official_semantic_patch_cycle_closure_323o_closure.json", closure_json)
    write_excel(
        output_dir / "official_semantic_patch_cycle_closure_323o_summary.xlsx",
        {
            "summary": pd.DataFrame([summary]),
            "cycle_summary": pd.DataFrame(),
            "stage_alignment": pd.DataFrame(),
            "warnings": pd.DataFrame(),
            "remaining_risks": pd.DataFrame(),
            "next_cycle_recommendations": pd.DataFrame(),
            "qa_summary": pd.DataFrame(
                [
                    {
                        "qa_pass_count": 0,
                        "qa_warn_count": 0,
                        "qa_fail_count": 1,
                        "blocking_reasons": code,
                        "decision": EXPECTED_323O_NOT_READY_DECISION,
                    }
                ]
            ),
            "qa_checks": pd.DataFrame(qa_json["checks"]),
            "known_limitations": pd.DataFrame(
                [{"limitation": "blocked_input", "detail": "Required upstream summary is missing."}]
            ),
        },
    )
    (output_dir / "official_semantic_patch_cycle_closure_323o_report.md").write_text(
        official_semantic_patch_cycle_closure_323o_markdown(summary),
        encoding="utf-8",
    )
    (output_dir / "official_semantic_patch_cycle_closure_323o_decision.md").write_text(
        official_semantic_patch_cycle_closure_323o_decision_markdown(decision_json),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 323O official semantic patch cycle closure report.")
    parser.add_argument("--reference-322o-dir", default=str(DEFAULT_REFERENCE_322O_DIR))
    parser.add_argument("--reference-322n-dir", default=str(DEFAULT_REFERENCE_322N_DIR))
    parser.add_argument("--reference-323n-dir", default=str(DEFAULT_REFERENCE_323N_DIR))
    parser.add_argument("--reference-323m-dir", default=str(DEFAULT_REFERENCE_323M_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    reference_322o_dir = Path(args.reference_322o_dir)
    reference_322n_dir = Path(args.reference_322n_dir)
    reference_323n_dir = Path(args.reference_323n_dir)
    reference_323m_dir = Path(args.reference_323m_dir)
    output_dir = Path(args.output_dir)

    required_files = [
        (reference_322o_dir / "post_patch_regression_validation_322o_summary.json", "BLOCKED_MISSING_322O_SUMMARY"),
        (reference_322n_dir / "official_semantic_patch_application_322n_summary.json", "BLOCKED_MISSING_322N_SUMMARY"),
        (reference_323n_dir / "post_patch_regression_validation_323n_summary.json", "BLOCKED_MISSING_323N_SUMMARY"),
        (reference_323m_dir / "official_patch_application_323m_summary.json", "BLOCKED_MISSING_323M_SUMMARY"),
    ]
    for path, code in required_files:
        if not path.exists():
            _blocked_result(output_dir, code)
            print(f"official_semantic_patch_cycle_closure_323o_summary_json: {output_dir / 'official_semantic_patch_cycle_closure_323o_summary.json'}")
            return 0

    inputs = load_official_semantic_patch_cycle_closure_323o_inputs(
        reference_322o_dir=reference_322o_dir,
        reference_322n_dir=reference_322n_dir,
        reference_323n_dir=reference_323n_dir,
        reference_323m_dir=reference_323m_dir,
    )
    artifacts = build_official_semantic_patch_cycle_closure_323o(
        summary_322o=inputs["summary_322o"],
        summary_322n=inputs["summary_322n"],
        summary_323n=inputs["summary_323n"],
        summary_323m=inputs["summary_323m"],
        qa_323n=inputs["qa_323n"],
        output_dir=output_dir,
    )

    summary = artifacts["summary"]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = {
        "summary_json": output_dir / "official_semantic_patch_cycle_closure_323o_summary.json",
        "qa_json": output_dir / "official_semantic_patch_cycle_closure_323o_qa.json",
        "closure_json": output_dir / "official_semantic_patch_cycle_closure_323o_closure.json",
        "summary_xlsx": output_dir / "official_semantic_patch_cycle_closure_323o_summary.xlsx",
        "report_md": output_dir / "official_semantic_patch_cycle_closure_323o_report.md",
        "decision_md": output_dir / "official_semantic_patch_cycle_closure_323o_decision.md",
    }

    sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "cycle_summary": artifacts["cycle_summary_df"],
        "stage_alignment": artifacts["stage_alignment_df"],
        "warnings": artifacts["warning_df"],
        "remaining_risks": artifacts["remaining_risks_df"],
        "next_cycle_recommendations": artifacts["recommendations_df"],
        "qa_summary": artifacts["qa_summary_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }

    write_json(output_files["summary_json"], summary)
    write_json(output_files["qa_json"], artifacts["qa_json"])
    write_json(output_files["closure_json"], artifacts["closure_json"])
    write_excel(output_files["summary_xlsx"], sheets)
    output_files["report_md"].write_text(
        official_semantic_patch_cycle_closure_323o_markdown(summary),
        encoding="utf-8",
    )
    output_files["decision_md"].write_text(
        official_semantic_patch_cycle_closure_323o_decision_markdown(artifacts["decision_json"]),
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
    summary["decision"] = EXPECTED_323O_READY_DECISION if summary["qa_fail_count"] == 0 else EXPECTED_323O_NOT_READY_DECISION

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
        official_semantic_patch_cycle_closure_323o_markdown(summary),
        encoding="utf-8",
    )
    output_files["decision_md"].write_text(
        official_semantic_patch_cycle_closure_323o_decision_markdown(
            {
                "decision": summary["decision"],
                "qa_fail_count": summary["qa_fail_count"],
                "blocking_reasons": summary["blocking_reasons"],
                "warning_323": summary["warning_323"],
                "next_step": (
                    "Proceed to next-cycle planning using remaining unresolved and warning-aware semantic opportunity mining."
                    if summary["qa_fail_count"] == 0
                    else "Review blocking reasons before declaring the cycle closed."
                ),
            }
        ),
        encoding="utf-8",
    )

    print(f"official_semantic_patch_cycle_closure_323o_summary_json: {output_files['summary_json']}")
    print(f"official_semantic_patch_cycle_closure_323o_qa_json: {output_files['qa_json']}")
    print(f"official_semantic_patch_cycle_closure_323o_closure_json: {output_files['closure_json']}")
    print(f"official_semantic_patch_cycle_closure_323o_summary_xlsx: {output_files['summary_xlsx']}")
    print(f"official_semantic_patch_cycle_closure_323o_report_md: {output_files['report_md']}")
    print(f"official_semantic_patch_cycle_closure_323o_decision_md: {output_files['decision_md']}")
    for key in [
        "rules_322",
        "trusted_gain_322",
        "review_reduction_322",
        "rules_323",
        "trusted_gain_323",
        "review_reduction_323",
        "combined_rules",
        "combined_trusted_gain",
        "combined_review_reduction",
        "warning_323",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
