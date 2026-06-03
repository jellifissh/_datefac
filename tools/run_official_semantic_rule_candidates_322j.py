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

from datefac.semantic.official_rule_candidates_sandbox_application import (
    build_official_rule_candidates_322j_sandbox_application,
    load_official_rule_candidates_322j_inputs,
)
from datefac.semantic.official_rule_candidates_sandbox_report import (
    AFFECTED_CANDIDATE_SHEET_ORDER,
    BEFORE_AFTER_SHEET_ORDER,
    official_rule_candidates_322j_report_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "322J",
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
        "trusted_total_before_322j": 0,
        "trusted_total_after_322j": 0,
        "review_required_total_before_322j": 0,
        "review_required_total_after_322j": 0,
        "rejected_total_before_322j": 0,
        "rejected_total_after_322j": 0,
        "trusted_gain_322j": 0,
        "review_reduction_322j": 0,
        "out_of_scope_or_rejected_gain_322j": 0,
        "affected_candidate_count": 0,
        "selected_core_trusted_rate_before_322j": 0,
        "selected_core_trusted_rate_after_322j": 0,
        "remaining_unknown_metric_candidate_count": 0,
        "remaining_unit_unknown_candidate_count": 0,
        "remaining_manual_review_count": 0,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "official_rule_candidates_322j_decision": "OFFICIAL_RULE_CANDIDATES_322J_NOT_READY_FOR_OFFICIAL_PATCH",
    }

    before_after_sheets = {
        "summary": pd.DataFrame([summary]),
        "before_after_overview": pd.DataFrame(),
        "rule_application_overview": pd.DataFrame(),
        "official_alias_rule_candidates": pd.DataFrame(),
        "official_scope_rule_candidates": pd.DataFrame(),
        "trusted_after_preview_322j": pd.DataFrame(),
        "review_required_after_preview_322j": pd.DataFrame(),
        "rejected_after_preview_322j": pd.DataFrame(),
        "remaining_review_burden_322j": pd.DataFrame(),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
        "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": "Required input is missing."}]),
    }
    affected_sheets = {
        "summary": pd.DataFrame([summary]),
        "candidate_before_after_diff_322j": pd.DataFrame(),
        "rule_application_log_322j": pd.DataFrame(),
        "affected_candidate_deltas_by_rule": pd.DataFrame(),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
    }

    write_excel(
        output_dir / "official_semantic_rule_candidates_322j_before_after_preview.xlsx",
        before_after_sheets,
        BEFORE_AFTER_SHEET_ORDER,
    )
    write_excel(
        output_dir / "official_semantic_rule_candidates_322j_affected_candidates.xlsx",
        affected_sheets,
        AFFECTED_CANDIDATE_SHEET_ORDER,
    )
    write_json(output_dir / "official_semantic_rule_candidates_322j_summary.json", summary)
    write_json(
        output_dir / "official_semantic_rule_candidates_322j_qa.json",
        {
            "qa_pass_count": 0,
            "qa_warn_count": 0,
            "qa_fail_count": 1,
            "blocking_reasons": [code],
            "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}],
        },
    )
    write_jsonl(output_dir / "official_semantic_rule_candidates_322j_rule_application_log.jsonl", pd.DataFrame())
    (output_dir / "official_semantic_rule_candidates_322j_report.md").write_text(
        official_rule_candidates_322j_report_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 322J official semantic rule candidates sandbox application.")
    parser.add_argument("--official-rule-candidate-dir", required=True)
    parser.add_argument("--trust-split-dir", required=True)
    parser.add_argument("--patch-preview-dir", required=False, default="")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    official_rule_candidate_dir = Path(args.official_rule_candidate_dir)
    trust_split_dir = Path(args.trust_split_dir)
    patch_preview_dir = Path(args.patch_preview_dir) if args.patch_preview_dir else None
    output_dir = Path(args.output_dir)

    if not official_rule_candidate_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_322I_OFFICIAL_RULE_CANDIDATE_DIR")
        print(f"official_rule_candidates_322j_summary_json: {output_dir / 'official_semantic_rule_candidates_322j_summary.json'}")
        return 0
    if not trust_split_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_322B2_TRUST_SPLIT_DIR")
        print(f"official_rule_candidates_322j_summary_json: {output_dir / 'official_semantic_rule_candidates_322j_summary.json'}")
        return 0

    inputs = load_official_rule_candidates_322j_inputs(
        official_rule_candidate_dir=official_rule_candidate_dir,
        trust_split_dir=trust_split_dir,
        patch_preview_dir=patch_preview_dir,
    )

    artifacts = build_official_rule_candidates_322j_sandbox_application(
        package_summary=inputs["package_summary"],
        alias_candidates=inputs["alias_candidates"],
        scope_candidates=inputs["scope_candidates"],
        trust_summary=inputs["trust_summary"],
        patch_summary=inputs["patch_summary"],
        selected_candidates_df=inputs["selected_candidates_df"],
    )

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    before_after_preview_path = output_dir / "official_semantic_rule_candidates_322j_before_after_preview.xlsx"
    affected_candidates_path = output_dir / "official_semantic_rule_candidates_322j_affected_candidates.xlsx"
    summary_json_path = output_dir / "official_semantic_rule_candidates_322j_summary.json"
    qa_json_path = output_dir / "official_semantic_rule_candidates_322j_qa.json"
    report_md_path = output_dir / "official_semantic_rule_candidates_322j_report.md"
    rule_application_log_jsonl_path = output_dir / "official_semantic_rule_candidates_322j_rule_application_log.jsonl"

    before_after_sheets = {
        "summary": pd.DataFrame([summary]),
        "before_after_overview": artifacts["before_after_overview_df"],
        "rule_application_overview": artifacts["rule_application_overview_df"],
        "official_alias_rule_candidates": artifacts["official_alias_rule_candidates_df"],
        "official_scope_rule_candidates": artifacts["official_scope_rule_candidates_df"],
        "trusted_after_preview_322j": artifacts["trusted_after_preview_df"],
        "review_required_after_preview_322j": artifacts["review_required_after_preview_df"],
        "rejected_after_preview_322j": artifacts["rejected_after_preview_df"],
        "remaining_review_burden_322j": artifacts["remaining_review_burden_322j_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }
    affected_sheets = {
        "summary": pd.DataFrame([summary]),
        "candidate_before_after_diff_322j": artifacts["candidate_before_after_diff_df"],
        "rule_application_log_322j": artifacts["rule_application_log_df"],
        "affected_candidate_deltas_by_rule": artifacts["affected_candidate_deltas_by_rule_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }

    write_excel(before_after_preview_path, before_after_sheets, BEFORE_AFTER_SHEET_ORDER)
    write_excel(affected_candidates_path, affected_sheets, AFFECTED_CANDIDATE_SHEET_ORDER)
    write_json(summary_json_path, summary)
    write_json(
        qa_json_path,
        {
            "qa_pass_count": summary.get("qa_pass_count", 0),
            "qa_warn_count": summary.get("qa_warn_count", 0),
            "qa_fail_count": summary.get("qa_fail_count", 0),
            "blocking_reasons": summary.get("blocking_reasons", []),
            "checks": artifacts["qa_checks_df"].to_dict(orient="records"),
        },
    )
    report_md_path.write_text(official_rule_candidates_322j_report_markdown(summary), encoding="utf-8")
    write_jsonl(rule_application_log_jsonl_path, artifacts["rule_application_log_df"])

    output_files_written = all(
        path.exists()
        for path in [
            before_after_preview_path,
            affected_candidates_path,
            summary_json_path,
            qa_json_path,
            report_md_path,
            rule_application_log_jsonl_path,
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
    summary["official_rule_candidates_322j_decision"] = (
        "OFFICIAL_RULE_CANDIDATES_322J_READY_FOR_322K_CONTROLLED_OFFICIAL_PATCH_PROPOSAL"
        if summary["qa_fail_count"] == 0
        else "OFFICIAL_RULE_CANDIDATES_322J_NOT_READY_FOR_OFFICIAL_PATCH"
    )

    before_after_sheets["summary"] = pd.DataFrame([summary])
    before_after_sheets["qa_checks"] = qa_df
    affected_sheets["summary"] = pd.DataFrame([summary])
    affected_sheets["qa_checks"] = qa_df
    write_excel(before_after_preview_path, before_after_sheets, BEFORE_AFTER_SHEET_ORDER)
    write_excel(affected_candidates_path, affected_sheets, AFFECTED_CANDIDATE_SHEET_ORDER)
    write_json(summary_json_path, summary)
    write_json(
        qa_json_path,
        {
            "qa_pass_count": summary.get("qa_pass_count", 0),
            "qa_warn_count": summary.get("qa_warn_count", 0),
            "qa_fail_count": summary.get("qa_fail_count", 0),
            "blocking_reasons": summary.get("blocking_reasons", []),
            "checks": qa_df.to_dict(orient="records"),
        },
    )
    report_md_path.write_text(official_rule_candidates_322j_report_markdown(summary), encoding="utf-8")

    print(f"official_rule_candidates_322j_before_after_preview_xlsx: {before_after_preview_path}")
    print(f"official_rule_candidates_322j_affected_candidates_xlsx: {affected_candidates_path}")
    print(f"official_rule_candidates_322j_summary_json: {summary_json_path}")
    print(f"official_rule_candidates_322j_qa_json: {qa_json_path}")
    print(f"official_rule_candidates_322j_report_md: {report_md_path}")
    print(f"official_rule_candidates_322j_rule_application_log_jsonl: {rule_application_log_jsonl_path}")
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
        "trusted_total_before_322j",
        "trusted_total_after_322j",
        "review_required_total_before_322j",
        "review_required_total_after_322j",
        "rejected_total_before_322j",
        "rejected_total_after_322j",
        "trusted_gain_322j",
        "review_reduction_322j",
        "out_of_scope_or_rejected_gain_322j",
        "affected_candidate_count",
        "selected_core_trusted_rate_before_322j",
        "selected_core_trusted_rate_after_322j",
        "remaining_unknown_metric_candidate_count",
        "remaining_unit_unknown_candidate_count",
        "remaining_manual_review_count",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "official_rule_candidates_322j_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
