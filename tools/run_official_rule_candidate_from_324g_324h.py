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

from datefac.semantic.official_rule_candidate_from_324g_324h import (  # noqa: E402
    NOT_READY_DECISION,
    build_official_rule_candidate_from_324g_324h,
    load_official_rule_candidate_from_324g_324h_inputs,
    _load_alias_reference,
    _load_scope_reference,
)
from datefac.semantic.official_rule_candidate_from_324g_324h_report import (  # noqa: E402
    official_rule_candidate_from_324g_324h_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "324H",
        "output_dir": str(output_dir),
        "source_sandbox_rule_count": 0,
        "candidate_count": 0,
        "scope_candidate_count": 0,
        "ready_for_controlled_proposal_count": 0,
        "needs_review_candidate_count": 0,
        "rejected_candidate_count": 0,
        "duplicate_candidate_id_count": 0,
        "already_official_overlap_count": 0,
        "alias_conflict_count": 0,
        "conflict_count": 0,
        "missing_target_asset_or_group_count": 0,
        "missing_provenance_count": 0,
        "affected_candidate_count": 0,
        "expected_trusted_gain": 0,
        "expected_review_reduction": 0,
        "expected_out_of_scope_or_rejected_gain": 0,
        "carried_warnings": [],
        "official_assets_not_modified_confirmed": True,
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
        output_dir / "official_rule_candidate_from_324g_324h_summary.json", summary
    )
    write_json(output_dir / "official_rule_candidate_from_324g_324h_qa.json", qa_json)
    write_json(
        output_dir / "official_rule_candidate_from_324g_324h_candidate_package.json",
        {
            "stage": "324H",
            "decision": NOT_READY_DECISION,
            "effective_unique_candidates": [],
            "scope_candidates": [],
            "candidate_source_bridge": [],
            "source_provenance": [],
        },
    )
    write_jsonl(
        output_dir / "official_rule_candidate_from_324g_324h_effective_candidates.jsonl",
        empty,
    )
    write_jsonl(
        output_dir / "official_rule_candidate_from_324g_324h_source_provenance.jsonl",
        empty,
    )
    write_excel(
        output_dir / "official_rule_candidate_from_324g_324h.xlsx",
        {
            "summary": pd.DataFrame([summary]),
            "effective_unique_candidates": empty,
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
        output_dir / "official_rule_candidate_from_324g_324h_report.md"
    ).write_text(
        official_rule_candidate_from_324g_324h_markdown(summary), encoding="utf-8"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 324H official rule candidate packaging from 324G sandbox replay."
    )
    parser.add_argument("--sandbox-replay-dir", required=True)
    parser.add_argument("--human-confirmation-reviewed-dir", required=True)
    parser.add_argument("--response-schema-validation-dir", required=True)
    parser.add_argument("--safe-adjudicator-request-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    sandbox_replay_dir = Path(args.sandbox_replay_dir)
    human_confirmation_reviewed_dir = Path(args.human_confirmation_reviewed_dir)
    response_schema_validation_dir = Path(args.response_schema_validation_dir)
    safe_adjudicator_request_dir = Path(args.safe_adjudicator_request_dir)
    output_dir = Path(args.output_dir)

    required_dirs = [
        (sandbox_replay_dir, "BLOCKED_MISSING_324G_SANDBOX_REPLAY_DIR"),
        (
            human_confirmation_reviewed_dir,
            "BLOCKED_MISSING_324F_HUMAN_CONFIRMATION_REVIEWED_DIR",
        ),
        (
            response_schema_validation_dir,
            "BLOCKED_MISSING_324E_RESPONSE_SCHEMA_VALIDATION_DIR",
        ),
        (safe_adjudicator_request_dir, "BLOCKED_MISSING_324C_SAFE_REQUEST_DIR"),
    ]
    for directory, code in required_dirs:
        if not directory.exists():
            _blocked_result(output_dir, code)
            print(
                "official_rule_candidate_from_324g_324h_summary_json: "
                f"{output_dir / 'official_rule_candidate_from_324g_324h_summary.json'}"
            )
            return 0

    inputs = load_official_rule_candidate_from_324g_324h_inputs(
        sandbox_replay_dir=sandbox_replay_dir,
        human_confirmation_reviewed_dir=human_confirmation_reviewed_dir,
        response_schema_validation_dir=response_schema_validation_dir,
        safe_adjudicator_request_dir=safe_adjudicator_request_dir,
    )
    scope_reference_loaded, _, scope_reference_df = _load_scope_reference()
    alias_reference_loaded, _, alias_reference_df = _load_alias_reference()

    artifacts = build_official_rule_candidate_from_324g_324h(
        sandbox_summary=inputs["sandbox_summary"],
        sandbox_qa=inputs["sandbox_qa"],
        sandbox_rule_set=inputs["sandbox_rule_set"],
        sandbox_rule_application_log_df=inputs["sandbox_rule_application_log_df"],
        human_confirmation_summary=inputs["human_confirmation_summary"],
        human_confirmation_outcome=inputs["human_confirmation_outcome"],
        response_schema_validation_summary=inputs["response_schema_validation_summary"],
        validated_responses_df=inputs["validated_responses_df"],
        accepted_for_human_confirmation=inputs["accepted_for_human_confirmation"],
        safe_request_package=inputs["safe_request_package"],
        raw_responses_df=inputs["raw_responses_df"],
        response_collection_summary=inputs["response_collection_summary"],
        scope_reference_loaded=scope_reference_loaded,
        scope_reference_df=scope_reference_df,
        alias_reference_loaded=alias_reference_loaded,
        alias_reference_df=alias_reference_df,
    )

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_json_path = output_dir / "official_rule_candidate_from_324g_324h_summary.json"
    qa_json_path = output_dir / "official_rule_candidate_from_324g_324h_qa.json"
    workbook_path = output_dir / "official_rule_candidate_from_324g_324h.xlsx"
    report_md_path = output_dir / "official_rule_candidate_from_324g_324h_report.md"
    package_json_path = (
        output_dir / "official_rule_candidate_from_324g_324h_candidate_package.json"
    )
    effective_candidates_jsonl_path = (
        output_dir / "official_rule_candidate_from_324g_324h_effective_candidates.jsonl"
    )
    source_provenance_jsonl_path = (
        output_dir / "official_rule_candidate_from_324g_324h_source_provenance.jsonl"
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
        official_rule_candidate_from_324g_324h_markdown(summary), encoding="utf-8"
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
        official_rule_candidate_from_324g_324h_markdown(summary), encoding="utf-8"
    )

    print(f"official_rule_candidate_from_324g_324h_summary_json: {summary_json_path}")
    print(f"official_rule_candidate_from_324g_324h_qa_json: {qa_json_path}")
    print(f"official_rule_candidate_from_324g_324h_workbook: {workbook_path}")
    print(f"official_rule_candidate_from_324g_324h_report_md: {report_md_path}")
    print(f"official_rule_candidate_from_324g_324h_package_json: {package_json_path}")
    print(
        "official_rule_candidate_from_324g_324h_effective_candidates_jsonl: "
        f"{effective_candidates_jsonl_path}"
    )
    print(
        "official_rule_candidate_from_324g_324h_source_provenance_jsonl: "
        f"{source_provenance_jsonl_path}"
    )
    for key in [
        "source_sandbox_rule_count",
        "candidate_count",
        "scope_candidate_count",
        "ready_for_controlled_proposal_count",
        "needs_review_candidate_count",
        "rejected_candidate_count",
        "duplicate_candidate_id_count",
        "already_official_overlap_count",
        "alias_conflict_count",
        "conflict_count",
        "affected_candidate_count",
        "expected_trusted_gain",
        "expected_review_reduction",
        "expected_out_of_scope_or_rejected_gain",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
