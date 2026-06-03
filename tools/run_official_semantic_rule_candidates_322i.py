from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.semantic.official_rule_candidates import (
    build_official_rule_candidates,
    load_official_rule_candidate_inputs,
)
from datefac.semantic.official_rule_candidates_report import (
    official_rule_candidates_report_markdown,
    write_excel,
    write_json,
)


def _write_json_array(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "322I",
        "output_dir": str(output_dir),
        "input_official_rule_candidate_count": 0,
        "alias_rule_candidate_count": 0,
        "scope_rule_candidate_count": 0,
        "unit_rule_candidate_count": 0,
        "rejected_noise_rule_candidate_count": 0,
        "duplicate_rule_candidate_count": 0,
        "conflict_rule_candidate_count": 0,
        "ready_for_sandbox_application_count": 0,
        "needs_additional_review_count": 0,
        "affected_candidate_count": 0,
        "expected_trusted_gain": 0,
        "expected_review_reduction": 0,
        "expected_out_of_scope_or_rejected_gain": 0,
        "remaining_unknown_metric_candidate_count": 0,
        "remaining_unit_unknown_candidate_count": 0,
        "remaining_manual_review_count": 0,
        "official_reference_scope_rules_loaded": False,
        "official_reference_override_loaded": False,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "official_rule_candidates_decision": code,
    }
    sheets = {
        "summary": pd.DataFrame([summary]),
        "official_alias_rule_candidates": pd.DataFrame(),
        "official_scope_rule_candidates": pd.DataFrame(),
        "candidate_impact_evidence": pd.DataFrame(),
        "duplicate_conflict_audit": pd.DataFrame(),
        "official_patch_json_preview": pd.DataFrame(),
        "human_approval_checklist": pd.DataFrame(),
        "remaining_review_burden_after_candidate_rules": pd.DataFrame(),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
        "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": "Required input is missing."}]),
    }
    write_excel(output_dir / "official_semantic_rule_candidates_322i.xlsx", sheets)
    write_json(output_dir / "official_semantic_rule_candidates_322i_summary.json", summary)
    (output_dir / "official_semantic_rule_candidates_322i_report.md").write_text(
        official_rule_candidates_report_markdown(summary),
        encoding="utf-8",
    )
    _write_json_array(output_dir / "alias_rule_candidates_322i.json", [])
    _write_json_array(output_dir / "scope_rule_candidates_322i.json", [])
    _write_json_array(output_dir / "official_rule_candidate_package_322i.json", {})
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 322I official semantic rule candidate packaging.")
    parser.add_argument("--patch-preview-dir", required=True)
    parser.add_argument("--proposal-dir", required=True)
    parser.add_argument("--adjudicator-apply-dir", required=True)
    parser.add_argument("--trust-split-dir", required=True)
    parser.add_argument("--formal-scope-rules", required=False, default="")
    parser.add_argument("--ai-repair-override", required=False, default="")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    patch_preview_dir = Path(args.patch_preview_dir)
    proposal_dir = Path(args.proposal_dir)
    adjudicator_apply_dir = Path(args.adjudicator_apply_dir)
    trust_split_dir = Path(args.trust_split_dir)
    formal_scope_rules = Path(args.formal_scope_rules) if args.formal_scope_rules else Path("")
    ai_repair_override = Path(args.ai_repair_override) if args.ai_repair_override else Path("")
    output_dir = Path(args.output_dir)

    if not patch_preview_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_322H_PATCH_PREVIEW_DIR")
        print(f"official_rule_candidates_322i_summary_json: {output_dir / 'official_semantic_rule_candidates_322i_summary.json'}")
        return 0

    inputs = load_official_rule_candidate_inputs(
        patch_preview_dir=patch_preview_dir,
        proposal_dir=proposal_dir,
        adjudicator_apply_dir=adjudicator_apply_dir,
        trust_split_dir=trust_split_dir,
        formal_scope_rules=formal_scope_rules,
        ai_repair_override=ai_repair_override,
    )
    artifacts = build_official_rule_candidates(
        patch_summary=inputs["patch_summary"],
        proposal_summary=inputs["proposal_summary"],
        apply_summary=inputs["apply_summary"],
        trust_summary=inputs["trust_summary"],
        official_rule_candidate_preview_df=inputs["official_rule_candidate_preview_df"],
        candidate_diff_df=inputs["candidate_diff_df"],
        patch_impact_df=inputs["patch_impact_df"],
        reviewed_inventory_df=inputs["reviewed_inventory_df"],
        remaining_review_burden_df=inputs["remaining_review_burden_df"],
        scope_reference_loaded=inputs["scope_reference_loaded"],
        scope_reference_df=inputs["scope_reference_df"],
        override_reference_loaded=inputs["override_reference_loaded"],
        override_reference_df=inputs["override_reference_df"],
    )

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = {
        "excel": output_dir / "official_semantic_rule_candidates_322i.xlsx",
        "summary_json": output_dir / "official_semantic_rule_candidates_322i_summary.json",
        "report_md": output_dir / "official_semantic_rule_candidates_322i_report.md",
        "alias_json": output_dir / "alias_rule_candidates_322i.json",
        "scope_json": output_dir / "scope_rule_candidates_322i.json",
        "package_json": output_dir / "official_rule_candidate_package_322i.json",
    }

    sheets = {
        "summary": pd.DataFrame([summary]),
        "official_alias_rule_candidates": artifacts["official_alias_rule_candidates_df"],
        "official_scope_rule_candidates": artifacts["official_scope_rule_candidates_df"],
        "candidate_impact_evidence": artifacts["candidate_impact_evidence_df"],
        "duplicate_conflict_audit": artifacts["duplicate_conflict_audit_df"],
        "official_patch_json_preview": artifacts["official_patch_json_preview_df"],
        "human_approval_checklist": artifacts["human_approval_checklist_df"],
        "remaining_review_burden_after_candidate_rules": artifacts["remaining_review_burden_after_candidate_rules_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }

    write_excel(output_files["excel"], sheets)
    write_json(output_files["summary_json"], summary)
    output_files["report_md"].write_text(official_rule_candidates_report_markdown(summary), encoding="utf-8")
    _write_json_array(output_files["alias_json"], artifacts["alias_rule_candidates_json"])
    _write_json_array(output_files["scope_json"], artifacts["scope_rule_candidates_json"])
    _write_json_array(output_files["package_json"], artifacts["official_rule_candidate_package_json"])

    package_preview_df = artifacts["official_patch_json_preview_df"].copy()
    if not package_preview_df.empty:
        path_lookup = {
            "alias_rule_candidates_322i.json": str(output_files["alias_json"]),
            "scope_rule_candidates_322i.json": str(output_files["scope_json"]),
            "official_rule_candidate_package_322i.json": str(output_files["package_json"]),
        }
        package_preview_df["output_path"] = package_preview_df["artifact_name"].map(lambda name: path_lookup.get(str(name), ""))

    qa_df = artifacts["qa_checks_df"].copy()
    output_json_ok = True
    for path in [output_files["alias_json"], output_files["scope_json"], output_files["package_json"]]:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            output_json_ok = False
            break
    qa_df = pd.concat(
        [
            qa_df,
            pd.DataFrame(
                [
                    {
                        "check_name": "output_json_files_are_valid",
                        "status": "PASS" if output_json_ok else "FAIL",
                        "detail": "alias/scope/package JSON parsed successfully",
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    output_files_written = all(path.exists() for path in output_files.values())
    qa_df = pd.concat(
        [
            qa_df,
            pd.DataFrame(
                [
                    {
                        "check_name": "output_excel_json_report_written_successfully",
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
    if summary["qa_fail_count"] > 0:
        decision = "OFFICIAL_RULE_CANDIDATES_322I_BLOCKED_BY_QA_FAILURE"
    elif int(summary.get("conflict_rule_candidate_count", 0)) > 0:
        decision = "OFFICIAL_RULE_CANDIDATES_322I_NEEDS_CONFLICT_REVIEW"
    elif int(summary.get("ready_for_sandbox_application_count", 0)) > 0 and int(summary.get("expected_review_reduction", 0)) > 0:
        decision = "OFFICIAL_RULE_CANDIDATES_322I_READY_FOR_322J_SANDBOX_APPLICATION"
    elif int(summary.get("input_official_rule_candidate_count", 0)) > 0:
        decision = "OFFICIAL_RULE_CANDIDATES_322I_PARTIAL_NEEDS_REVIEW"
    else:
        decision = "OFFICIAL_RULE_CANDIDATES_322I_NO_RULE_CANDIDATES"
    summary["official_rule_candidates_decision"] = decision

    sheets["summary"] = pd.DataFrame([summary])
    sheets["official_patch_json_preview"] = package_preview_df
    sheets["qa_checks"] = qa_df
    write_excel(output_files["excel"], sheets)
    write_json(output_files["summary_json"], summary)
    output_files["report_md"].write_text(official_rule_candidates_report_markdown(summary), encoding="utf-8")

    print(f"official_rule_candidates_322i_excel: {output_files['excel']}")
    print(f"official_rule_candidates_322i_summary_json: {output_files['summary_json']}")
    print(f"official_rule_candidates_322i_report_md: {output_files['report_md']}")
    for key in [
        "input_official_rule_candidate_count",
        "alias_rule_candidate_count",
        "scope_rule_candidate_count",
        "unit_rule_candidate_count",
        "rejected_noise_rule_candidate_count",
        "duplicate_rule_candidate_count",
        "conflict_rule_candidate_count",
        "ready_for_sandbox_application_count",
        "needs_additional_review_count",
        "affected_candidate_count",
        "expected_trusted_gain",
        "expected_review_reduction",
        "expected_out_of_scope_or_rejected_gain",
        "remaining_unknown_metric_candidate_count",
        "remaining_unit_unknown_candidate_count",
        "remaining_manual_review_count",
        "official_reference_scope_rules_loaded",
        "official_reference_override_loaded",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "official_rule_candidates_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
