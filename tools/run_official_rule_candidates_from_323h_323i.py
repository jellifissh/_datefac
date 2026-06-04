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

from datefac.semantic.official_rule_candidates_from_323h import (  # noqa: E402
    NOT_READY_DECISION,
    build_official_rule_candidates_from_323h,
    load_official_rule_candidates_from_323h_inputs,
)
from datefac.semantic.official_rule_candidates_from_323h_report import (  # noqa: E402
    official_rule_candidates_from_323h_report_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "323I",
        "output_dir": str(output_dir),
        "source_sandbox_rule_count": 0,
        "source_sandbox_alias_rule_count": 0,
        "source_sandbox_scope_rule_count": 0,
        "effective_unique_candidate_count": 0,
        "alias_candidate_count": 0,
        "scope_candidate_count": 0,
        "ready_for_controlled_proposal_count": 0,
        "needs_review_candidate_count": 0,
        "rejected_candidate_count": 0,
        "duplicate_source_group_count": 0,
        "conflict_group_count": 0,
        "affected_candidate_count": 0,
        "trusted_gain_323i": 0,
        "review_reduction_323i": 0,
        "out_of_scope_or_rejected_gain_323i": 0,
        "carried_forward_core_false_exclusion_count": 0,
        "carried_forward_conflict_count": 0,
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
    empty = pd.DataFrame()
    write_json(
        output_dir / "official_rule_candidates_from_323h_323i_summary.json", summary
    )
    write_json(output_dir / "official_rule_candidates_from_323h_323i_qa.json", qa_json)
    write_json(
        output_dir / "official_rule_candidates_from_323h_323i_candidate_package.json",
        {
            "stage": "323I",
            "decision": NOT_READY_DECISION,
            "effective_unique_candidates": [],
            "alias_candidates": [],
            "scope_candidates": [],
            "candidate_source_bridge": [],
        },
    )
    write_jsonl(
        output_dir / "official_rule_candidates_from_323h_323i_effective_candidates.jsonl",
        empty,
    )
    write_jsonl(
        output_dir / "official_rule_candidates_from_323h_323i_source_provenance.jsonl",
        empty,
    )
    write_excel(
        output_dir / "official_rule_candidates_from_323h_323i.xlsx",
        {
            "summary": pd.DataFrame([summary]),
            "effective_unique_candidates": empty,
            "alias_candidates": empty,
            "scope_candidates": empty,
            "duplicate_source_groups": empty,
            "source_rule_inventory": empty,
            "source_provenance": empty,
            "candidate_source_bridge": empty,
            "qa_checks": pd.DataFrame(qa_json["checks"]),
            "known_limitations": pd.DataFrame(
                [{"limitation": "blocked_input", "detail": code}]
            ),
        },
    )
    (
        output_dir / "official_rule_candidates_from_323h_323i_report.md"
    ).write_text(
        official_rule_candidates_from_323h_report_markdown(summary), encoding="utf-8"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 323I official rule candidate packaging from 323H sandbox replay."
    )
    parser.add_argument("--sandbox-replay-dir", required=True)
    parser.add_argument("--reviewed-confirmation-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    sandbox_replay_dir = Path(args.sandbox_replay_dir)
    reviewed_confirmation_dir = Path(args.reviewed_confirmation_dir)
    output_dir = Path(args.output_dir)

    if not sandbox_replay_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_323H_SANDBOX_REPLAY_DIR")
        print(
            "official_rule_candidates_from_323h_323i_summary_json: "
            f"{output_dir / 'official_rule_candidates_from_323h_323i_summary.json'}"
        )
        return 0
    if not reviewed_confirmation_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_323G_REVIEWED_DIR")
        print(
            "official_rule_candidates_from_323h_323i_summary_json: "
            f"{output_dir / 'official_rule_candidates_from_323h_323i_summary.json'}"
        )
        return 0

    inputs = load_official_rule_candidates_from_323h_inputs(
        sandbox_replay_dir=sandbox_replay_dir,
        reviewed_confirmation_dir=reviewed_confirmation_dir,
    )
    artifacts = build_official_rule_candidates_from_323h(
        sandbox_summary=inputs["sandbox_summary"],
        sandbox_qa=inputs["sandbox_qa"],
        sandbox_rule_set=inputs["sandbox_rule_set"],
        sandbox_rule_application_log_df=inputs["sandbox_rule_application_log_df"],
        reviewed_summary=inputs["reviewed_summary"],
        reviewed_plan=inputs["reviewed_plan"],
    )

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_json_path = output_dir / "official_rule_candidates_from_323h_323i_summary.json"
    qa_json_path = output_dir / "official_rule_candidates_from_323h_323i_qa.json"
    workbook_path = output_dir / "official_rule_candidates_from_323h_323i.xlsx"
    report_md_path = output_dir / "official_rule_candidates_from_323h_323i_report.md"
    package_json_path = (
        output_dir / "official_rule_candidates_from_323h_323i_candidate_package.json"
    )
    effective_candidates_jsonl_path = (
        output_dir / "official_rule_candidates_from_323h_323i_effective_candidates.jsonl"
    )
    source_provenance_jsonl_path = (
        output_dir / "official_rule_candidates_from_323h_323i_source_provenance.jsonl"
    )

    write_json(summary_json_path, summary)
    write_json(qa_json_path, artifacts["qa_json"])
    write_json(package_json_path, artifacts["candidate_package_json"])
    write_jsonl(
        effective_candidates_jsonl_path, artifacts["effective_candidates_df"]
    )
    write_jsonl(source_provenance_jsonl_path, artifacts["source_provenance_df"])

    sheets = {
        "summary": pd.DataFrame([summary]),
        "effective_unique_candidates": artifacts["effective_candidates_df"],
        "alias_candidates": artifacts["alias_candidates_df"],
        "scope_candidates": artifacts["scope_candidates_df"],
        "duplicate_source_groups": artifacts["duplicate_groups_df"],
        "source_rule_inventory": artifacts["source_rule_inventory_df"],
        "source_provenance": artifacts["source_provenance_df"],
        "candidate_source_bridge": artifacts["candidate_source_bridge_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }
    write_excel(workbook_path, sheets)
    report_md_path.write_text(
        official_rule_candidates_from_323h_report_markdown(summary), encoding="utf-8"
    )

    outputs_written = all(
        path.exists()
        for path in [
            summary_json_path,
            qa_json_path,
            workbook_path,
            report_md_path,
            package_json_path,
            effective_candidates_jsonl_path,
            source_provenance_jsonl_path,
        ]
    )

    qa_df = artifacts["qa_checks_df"].copy()
    qa_df = pd.concat(
        [
            qa_df,
            pd.DataFrame(
                [
                    {
                        "check_name": "output::artifacts_written_successfully",
                        "status": "PASS" if outputs_written else "FAIL",
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
        qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist()
        if not qa_df.empty
        else []
    )
    if summary["qa_fail_count"] > 0:
        summary["decision"] = NOT_READY_DECISION

    artifacts["qa_json"]["qa_pass_count"] = summary["qa_pass_count"]
    artifacts["qa_json"]["qa_warn_count"] = summary["qa_warn_count"]
    artifacts["qa_json"]["qa_fail_count"] = summary["qa_fail_count"]
    artifacts["qa_json"]["blocking_reasons"] = summary["blocking_reasons"]
    artifacts["qa_json"]["checks"] = qa_df.to_dict(orient="records")
    artifacts["candidate_package_json"]["decision"] = summary["decision"]

    write_json(summary_json_path, summary)
    write_json(qa_json_path, artifacts["qa_json"])
    write_json(package_json_path, artifacts["candidate_package_json"])
    sheets["summary"] = pd.DataFrame([summary])
    sheets["qa_checks"] = qa_df
    write_excel(workbook_path, sheets)
    report_md_path.write_text(
        official_rule_candidates_from_323h_report_markdown(summary), encoding="utf-8"
    )

    print(f"official_rule_candidates_from_323h_323i_summary_json: {summary_json_path}")
    print(f"official_rule_candidates_from_323h_323i_qa_json: {qa_json_path}")
    print(f"official_rule_candidates_from_323h_323i_workbook: {workbook_path}")
    print(f"official_rule_candidates_from_323h_323i_report_md: {report_md_path}")
    print(f"official_rule_candidates_from_323h_323i_package_json: {package_json_path}")
    print(
        "official_rule_candidates_from_323h_323i_effective_candidates_jsonl: "
        f"{effective_candidates_jsonl_path}"
    )
    print(
        "official_rule_candidates_from_323h_323i_source_provenance_jsonl: "
        f"{source_provenance_jsonl_path}"
    )
    for key in [
        "source_sandbox_rule_count",
        "source_sandbox_alias_rule_count",
        "source_sandbox_scope_rule_count",
        "effective_unique_candidate_count",
        "alias_candidate_count",
        "scope_candidate_count",
        "ready_for_controlled_proposal_count",
        "needs_review_candidate_count",
        "rejected_candidate_count",
        "duplicate_source_group_count",
        "conflict_group_count",
        "affected_candidate_count",
        "trusted_gain_323i",
        "review_reduction_323i",
        "out_of_scope_or_rejected_gain_323i",
        "carried_forward_core_false_exclusion_count",
        "carried_forward_conflict_count",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
