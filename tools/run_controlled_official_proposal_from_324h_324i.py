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

from datefac.semantic.controlled_official_proposal_from_324h_324i import (  # noqa: E402
    FORMAL_SCOPE_RULES_PATH,
    NOT_READY_DECISION,
    OFFICIAL_ALIAS_ASSET_PATH,
    READY_DECISION,
    READY_WARN_DECISION,
    build_controlled_official_proposal_from_324h,
    load_controlled_official_proposal_from_324h_inputs,
    _load_alias_reference,
    _load_scope_reference,
)
from datefac.semantic.controlled_official_proposal_from_324h_324i_report import (  # noqa: E402
    controlled_official_proposal_from_324h_report_markdown,
    write_excel,
    write_json,
)


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "__MISSING__"
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "324I",
        "output_dir": str(output_dir),
        "loaded_ready_candidate_count": 0,
        "proposal_count": 0,
        "alias_proposal_count": 0,
        "scope_proposal_count": 0,
        "ready_for_dry_run_proposal_count": 0,
        "needs_review_proposal_count": 0,
        "rejected_proposal_count": 0,
        "target_asset_plan_count": 0,
        "target_asset_file_count": 0,
        "duplicate_proposal_id_count": 0,
        "already_official_overlap_count": 0,
        "alias_conflict_count": 0,
        "target_conflict_count": 0,
        "missing_target_asset_or_group_count": 0,
        "missing_provenance_count": 0,
        "expected_affected_candidate_count": 0,
        "expected_trusted_gain": 0,
        "expected_review_reduction": 0,
        "expected_out_of_scope_or_rejected_gain": 0,
        "carried_warnings": [],
        "proposal_only_no_apply_confirmed": True,
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
        output_dir / "controlled_official_proposal_from_324h_324i_summary.json",
        summary,
    )
    write_json(
        output_dir / "controlled_official_proposal_from_324h_324i_qa.json",
        qa_json,
    )
    write_json(
        output_dir / "controlled_official_proposal_from_324h_324i_proposal_package.json",
        {
            "stage": "324I",
            "decision": NOT_READY_DECISION,
            "controlled_proposals": [],
            "alias_proposals": [],
            "scope_proposals": [],
            "target_asset_plan": [],
            "proposal_source_bridge": [],
            "provenance_samples": [],
        },
    )
    write_json(
        output_dir / "controlled_official_proposal_from_324h_324i_alias_proposals.json",
        {"alias_proposals": []},
    )
    write_json(
        output_dir / "controlled_official_proposal_from_324h_324i_scope_proposals.json",
        {"scope_proposals": []},
    )
    write_excel(
        output_dir / "controlled_official_proposal_from_324h_324i_proposals.xlsx",
        {
            "summary": pd.DataFrame([summary]),
            "proposal_overview": empty,
            "alias_proposals": empty,
            "scope_proposals": empty,
            "target_asset_plan": empty,
            "proposal_source_bridge": empty,
            "provenance_samples": empty,
            "qa_summary": pd.DataFrame([{"qa_fail_count": 1, "decision": NOT_READY_DECISION}]),
            "qa_checks": pd.DataFrame(qa_json["checks"]),
            "known_limitations": pd.DataFrame(
                [{"limitation": "blocked_input", "detail": code}]
            ),
        },
    )
    (
        output_dir / "controlled_official_proposal_from_324h_324i_review_notes.md"
    ).write_text(
        controlled_official_proposal_from_324h_report_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 324I controlled official proposal packaging from 324H."
    )
    parser.add_argument(
        "--official-rule-candidate-dir",
        default=r"D:\_datefac\output\official_rule_candidate_from_324g_324h",
    )
    parser.add_argument(
        "--sandbox-replay-dir",
        default=r"D:\_datefac\output\scope_noise_human_confirmed_sandbox_replay_324g",
    )
    parser.add_argument(
        "--output-dir",
        default=r"D:\_datefac\output\controlled_official_proposal_from_324h_324i",
    )
    args = parser.parse_args()

    official_rule_candidate_dir = Path(args.official_rule_candidate_dir)
    sandbox_replay_dir = Path(args.sandbox_replay_dir)
    output_dir = Path(args.output_dir)

    if not official_rule_candidate_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_324H_OFFICIAL_RULE_CANDIDATE_DIR")
        print(
            "controlled_official_proposal_from_324h_324i_summary_json: "
            f"{output_dir / 'controlled_official_proposal_from_324h_324i_summary.json'}"
        )
        return 0
    if not sandbox_replay_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_324G_SANDBOX_REPLAY_DIR")
        print(
            "controlled_official_proposal_from_324h_324i_summary_json: "
            f"{output_dir / 'controlled_official_proposal_from_324h_324i_summary.json'}"
        )
        return 0

    alias_hash_before = _sha256_file(OFFICIAL_ALIAS_ASSET_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    inputs = load_controlled_official_proposal_from_324h_inputs(
        official_rule_candidate_dir=official_rule_candidate_dir,
        sandbox_replay_dir=sandbox_replay_dir,
    )
    alias_loaded, _, alias_reference_df = _load_alias_reference()
    scope_loaded, _, scope_reference_df = _load_scope_reference()
    artifacts = build_controlled_official_proposal_from_324h(
        official_rule_candidate_summary=inputs["official_rule_candidate_summary"],
        official_rule_candidate_qa=inputs["official_rule_candidate_qa"],
        effective_candidates_df=inputs["effective_candidates_df"],
        scope_candidates_df=inputs["scope_candidates_df"],
        candidate_source_bridge_df=inputs["candidate_source_bridge_df"],
        source_provenance_df=inputs["source_provenance_df"],
        sandbox_summary=inputs["sandbox_summary"],
        sandbox_qa=inputs["sandbox_qa"],
        alias_reference_loaded=alias_loaded,
        alias_reference_df=alias_reference_df,
        scope_reference_loaded=scope_loaded,
        scope_reference_df=scope_reference_df,
    )

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    excel_path = output_dir / "controlled_official_proposal_from_324h_324i_proposals.xlsx"
    summary_json_path = output_dir / "controlled_official_proposal_from_324h_324i_summary.json"
    qa_json_path = output_dir / "controlled_official_proposal_from_324h_324i_qa.json"
    package_json_path = (
        output_dir / "controlled_official_proposal_from_324h_324i_proposal_package.json"
    )
    alias_json_path = (
        output_dir / "controlled_official_proposal_from_324h_324i_alias_proposals.json"
    )
    scope_json_path = (
        output_dir / "controlled_official_proposal_from_324h_324i_scope_proposals.json"
    )
    notes_md_path = (
        output_dir / "controlled_official_proposal_from_324h_324i_review_notes.md"
    )

    sheets = {
        "summary": pd.DataFrame([summary]),
        "proposal_overview": artifacts["proposal_overview_df"],
        "alias_proposals": artifacts["alias_proposals_df"],
        "scope_proposals": artifacts["scope_proposals_df"],
        "target_asset_plan": artifacts["target_asset_plan_df"],
        "proposal_source_bridge": artifacts["proposal_source_bridge_df"],
        "provenance_samples": artifacts["provenance_samples_df"],
        "qa_summary": artifacts["qa_summary_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }
    write_excel(excel_path, sheets)
    write_json(summary_json_path, summary)
    write_json(qa_json_path, artifacts["qa_json"])
    write_json(package_json_path, artifacts["proposal_package_json"])
    write_json(
        alias_json_path,
        {"alias_proposals": artifacts["alias_proposals_df"].to_dict(orient="records")},
    )
    write_json(
        scope_json_path,
        {"scope_proposals": artifacts["scope_proposals_df"].to_dict(orient="records")},
    )
    notes_md_path.write_text(artifacts["notes_markdown"], encoding="utf-8")

    alias_hash_after = _sha256_file(OFFICIAL_ALIAS_ASSET_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    official_assets_unchanged = (
        alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after
    )

    qa_df = artifacts["qa_checks_df"].copy()
    qa_df = pd.concat(
        [
            qa_df,
            pd.DataFrame(
                [
                    {
                        "check_name": "safety::official_assets_not_modified",
                        "status": "PASS" if official_assets_unchanged else "FAIL",
                        "detail": (
                            f"alias_before={alias_hash_before} alias_after={alias_hash_after} "
                            f"scope_before={scope_hash_before} scope_after={scope_hash_after}"
                        ),
                    },
                    {
                        "check_name": "output::artifacts_written_successfully",
                        "status": "PASS"
                        if all(
                            path.exists()
                            for path in [
                                excel_path,
                                summary_json_path,
                                qa_json_path,
                                package_json_path,
                                alias_json_path,
                                scope_json_path,
                                notes_md_path,
                            ]
                        )
                        else "FAIL",
                        "detail": str(output_dir),
                    },
                ]
            ),
        ],
        ignore_index=True,
    )

    summary["official_assets_not_modified_confirmed"] = official_assets_unchanged
    summary["qa_pass_count"] = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    summary["qa_warn_count"] = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    summary["qa_fail_count"] = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    summary["blocking_reasons"] = (
        qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist()
        if not qa_df.empty
        else []
    )
    summary["decision"] = (
        NOT_READY_DECISION
        if summary["qa_fail_count"] > 0
        else READY_WARN_DECISION
        if summary["qa_warn_count"] > 0
        else READY_DECISION
    )

    artifacts["qa_json"]["qa_pass_count"] = summary["qa_pass_count"]
    artifacts["qa_json"]["qa_warn_count"] = summary["qa_warn_count"]
    artifacts["qa_json"]["qa_fail_count"] = summary["qa_fail_count"]
    artifacts["qa_json"]["blocking_reasons"] = summary["blocking_reasons"]
    artifacts["qa_json"]["checks"] = qa_df.to_dict(orient="records")
    artifacts["proposal_package_json"]["decision"] = summary["decision"]

    sheets["summary"] = pd.DataFrame([summary])
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

    write_excel(excel_path, sheets)
    write_json(summary_json_path, summary)
    write_json(qa_json_path, artifacts["qa_json"])
    write_json(package_json_path, artifacts["proposal_package_json"])
    notes_md_path.write_text(
        controlled_official_proposal_from_324h_report_markdown(summary),
        encoding="utf-8",
    )

    print(f"controlled_official_proposal_from_324h_324i_excel: {excel_path}")
    print(f"controlled_official_proposal_from_324h_324i_summary_json: {summary_json_path}")
    print(f"controlled_official_proposal_from_324h_324i_qa_json: {qa_json_path}")
    print(f"controlled_official_proposal_from_324h_324i_package_json: {package_json_path}")
    print(f"controlled_official_proposal_from_324h_324i_alias_json: {alias_json_path}")
    print(f"controlled_official_proposal_from_324h_324i_scope_json: {scope_json_path}")
    print(f"controlled_official_proposal_from_324h_324i_review_notes_md: {notes_md_path}")
    for key in [
        "loaded_ready_candidate_count",
        "proposal_count",
        "alias_proposal_count",
        "scope_proposal_count",
        "ready_for_dry_run_proposal_count",
        "needs_review_proposal_count",
        "rejected_proposal_count",
        "duplicate_proposal_id_count",
        "already_official_overlap_count",
        "alias_conflict_count",
        "target_conflict_count",
        "expected_affected_candidate_count",
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
