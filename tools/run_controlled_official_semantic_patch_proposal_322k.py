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

from datefac.semantic.controlled_official_patch_proposal import (
    EXPECTED_NEXT_DECISION,
    build_controlled_patch_proposals,
    load_controlled_patch_proposal_inputs,
)
from datefac.semantic.controlled_official_patch_proposal_report import (
    controlled_patch_proposal_report_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "322K",
        "output_dir": str(output_dir),
        "sandbox_readiness_passed": False,
        "sandbox_readiness_source_decision": "",
        "sandbox_readiness_source_qa_fail_count": 1,
        "total_patch_proposal_count": 0,
        "alias_patch_proposal_count": 0,
        "scope_patch_proposal_count": 0,
        "unit_patch_proposal_count": 0,
        "rejected_noise_patch_proposal_count": 0,
        "expected_affected_candidate_count": 0,
        "expected_trusted_gain": 0,
        "expected_review_reduction": 0,
        "expected_out_of_scope_or_rejected_gain": 0,
        "proposal_only_no_apply_confirmed": True,
        "official_files_not_modified_confirmed": True,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "controlled_official_patch_proposal_decision": "CONTROLLED_OFFICIAL_SEMANTIC_PATCH_PROPOSAL_322K_NOT_READY",
    }
    sheets = {
        "summary": pd.DataFrame([summary]),
        "alias_patch_proposals": pd.DataFrame(),
        "scope_patch_proposals": pd.DataFrame(),
        "proposal_overview": pd.DataFrame(),
        "qa_summary": pd.DataFrame([{"qa_pass_count": 0, "qa_warn_count": 0, "qa_fail_count": 1, "blocking_reasons": code, "decision": summary["controlled_official_patch_proposal_decision"]}]),
        "no_apply_proof": pd.DataFrame([{"proposal_only_decision": True, "files_read_count": 0, "files_written_count": 0, "official_files_not_modified_count": 0, "output_only_write_confirmation": True, "decision": "proposal_only_no_apply"}]),
        "risk_notes": pd.DataFrame(),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
        "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": "Required input is missing."}]),
    }
    write_excel(output_dir / "controlled_official_semantic_patch_proposal_322k_patch_proposals.xlsx", sheets)
    write_json(output_dir / "controlled_official_semantic_patch_proposal_322k_summary.json", summary)
    write_json(output_dir / "controlled_official_semantic_patch_proposal_322k_alias_patch_proposals.json", {"alias_patch_proposals": []})
    write_json(output_dir / "controlled_official_semantic_patch_proposal_322k_scope_patch_proposals.json", {"scope_patch_proposals": []})
    write_json(output_dir / "controlled_official_semantic_patch_proposal_322k_qa.json", {"qa_pass_count": 0, "qa_warn_count": 0, "qa_fail_count": 1, "blocking_reasons": [code], "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}]})
    write_json(output_dir / "controlled_official_semantic_patch_proposal_322k_no_apply_proof.json", {"proposal_only_decision": True, "files_read": [], "files_written": [], "official_files_not_modified": [], "output_only_write_confirmation": True, "decision": "proposal_only_no_apply"})
    (output_dir / "controlled_official_semantic_patch_proposal_322k_review_notes.md").write_text(
        controlled_patch_proposal_report_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 322K controlled official semantic patch proposal.")
    parser.add_argument("--sandbox-application-dir", default=r"D:\_datefac\output\official_semantic_rule_candidates_322j")
    parser.add_argument("--official-rule-candidate-dir", default=r"D:\_datefac\output\official_semantic_rule_candidates_322i")
    parser.add_argument("--output-dir", default=r"D:\_datefac\output\controlled_official_semantic_patch_proposal_322k")
    args = parser.parse_args()

    sandbox_application_dir = Path(args.sandbox_application_dir)
    official_rule_candidate_dir = Path(args.official_rule_candidate_dir)
    output_dir = Path(args.output_dir)

    if not sandbox_application_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_322J_SANDBOX_APPLICATION_DIR")
        print(f"controlled_official_patch_proposal_322k_summary_json: {output_dir / 'controlled_official_semantic_patch_proposal_322k_summary.json'}")
        return 0
    if not official_rule_candidate_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_322I_OFFICIAL_RULE_CANDIDATE_DIR")
        print(f"controlled_official_patch_proposal_322k_summary_json: {output_dir / 'controlled_official_semantic_patch_proposal_322k_summary.json'}")
        return 0

    inputs = load_controlled_patch_proposal_inputs(
        sandbox_application_dir=sandbox_application_dir,
        official_rule_candidate_dir=official_rule_candidate_dir,
    )
    artifacts = build_controlled_patch_proposals(
        sandbox_summary=inputs["sandbox_summary"],
        sandbox_qa=inputs["sandbox_qa"],
        sandbox_rule_application_log_df=inputs["sandbox_rule_application_log_df"],
        official_package_summary=inputs["official_package_summary"],
        alias_candidates=inputs["alias_candidates"],
        scope_candidates=inputs["scope_candidates"],
    )

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    excel_path = output_dir / "controlled_official_semantic_patch_proposal_322k_patch_proposals.xlsx"
    summary_json_path = output_dir / "controlled_official_semantic_patch_proposal_322k_summary.json"
    alias_json_path = output_dir / "controlled_official_semantic_patch_proposal_322k_alias_patch_proposals.json"
    scope_json_path = output_dir / "controlled_official_semantic_patch_proposal_322k_scope_patch_proposals.json"
    qa_json_path = output_dir / "controlled_official_semantic_patch_proposal_322k_qa.json"
    no_apply_proof_path = output_dir / "controlled_official_semantic_patch_proposal_322k_no_apply_proof.json"
    review_notes_path = output_dir / "controlled_official_semantic_patch_proposal_322k_review_notes.md"

    sheets = {
        "summary": pd.DataFrame([summary]),
        "alias_patch_proposals": artifacts["alias_patch_proposals_df"],
        "scope_patch_proposals": artifacts["scope_patch_proposals_df"],
        "proposal_overview": artifacts["proposal_overview_df"],
        "qa_summary": artifacts["qa_summary_df"],
        "no_apply_proof": artifacts["no_apply_proof_df"],
        "risk_notes": artifacts["risk_notes_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }
    write_excel(excel_path, sheets)
    write_json(summary_json_path, summary)
    write_json(alias_json_path, {"alias_patch_proposals": artifacts["alias_patch_proposals_json"]})
    write_json(scope_json_path, {"scope_patch_proposals": artifacts["scope_patch_proposals_json"]})
    write_json(qa_json_path, artifacts["qa_json"])
    write_json(no_apply_proof_path, artifacts["no_apply_proof_json"])
    review_notes_path.write_text(artifacts["review_notes_markdown"], encoding="utf-8")

    output_files_written = all(
        path.exists()
        for path in [
            excel_path,
            summary_json_path,
            alias_json_path,
            scope_json_path,
            qa_json_path,
            no_apply_proof_path,
            review_notes_path,
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
    summary["controlled_official_patch_proposal_decision"] = EXPECTED_NEXT_DECISION if summary["qa_fail_count"] == 0 else "CONTROLLED_OFFICIAL_SEMANTIC_PATCH_PROPOSAL_322K_NOT_READY"

    sheets["summary"] = pd.DataFrame([summary])
    sheets["qa_summary"] = pd.DataFrame(
        [
            {
                "qa_pass_count": summary["qa_pass_count"],
                "qa_warn_count": summary["qa_warn_count"],
                "qa_fail_count": summary["qa_fail_count"],
                "blocking_reasons": " | ".join(summary["blocking_reasons"]),
                "decision": summary["controlled_official_patch_proposal_decision"],
            }
        ]
    )
    sheets["qa_checks"] = qa_df
    write_excel(excel_path, sheets)
    write_json(summary_json_path, summary)
    write_json(
        qa_json_path,
        {
            "qa_pass_count": summary["qa_pass_count"],
            "qa_warn_count": summary["qa_warn_count"],
            "qa_fail_count": summary["qa_fail_count"],
            "blocking_reasons": summary["blocking_reasons"],
            "checks": qa_df.to_dict(orient="records"),
        },
    )
    review_notes_path.write_text(artifacts["review_notes_markdown"], encoding="utf-8")

    print(f"controlled_official_patch_proposal_322k_excel: {excel_path}")
    print(f"controlled_official_patch_proposal_322k_summary_json: {summary_json_path}")
    print(f"controlled_official_patch_proposal_322k_alias_json: {alias_json_path}")
    print(f"controlled_official_patch_proposal_322k_scope_json: {scope_json_path}")
    print(f"controlled_official_patch_proposal_322k_qa_json: {qa_json_path}")
    print(f"controlled_official_patch_proposal_322k_no_apply_proof_json: {no_apply_proof_path}")
    print(f"controlled_official_patch_proposal_322k_review_notes_md: {review_notes_path}")
    for key in [
        "total_patch_proposal_count",
        "alias_patch_proposal_count",
        "scope_patch_proposal_count",
        "unit_patch_proposal_count",
        "rejected_noise_patch_proposal_count",
        "expected_affected_candidate_count",
        "expected_trusted_gain",
        "expected_review_reduction",
        "expected_out_of_scope_or_rejected_gain",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "controlled_official_patch_proposal_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
