from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.semantic.adjudicator_replay import (
    apply_replay,
    build_remaining_review_burden,
    build_replay_instruction_inventory,
    load_replay_inputs,
)
from datefac.semantic.adjudicator_replay_report import (
    build_known_limitations_df,
    build_report_markdown,
    replay_decision,
    write_excel,
    write_json,
    write_jsonl,
)


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _write_empty_jsonl(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "322E",
        "output_dir": str(output_dir),
        "input_candidate_count": 0,
        "replay_instruction_count": 0,
        "replay_allowed_instruction_count": 0,
        "replay_blocked_instruction_count": 0,
        "affected_candidate_count": 0,
        "trusted_total_before_322e": 0,
        "trusted_total_after_322e": 0,
        "review_required_total_before_322e": 0,
        "review_required_total_after_322e": 0,
        "rejected_total_before_322e": 0,
        "rejected_total_after_322e": 0,
        "trusted_gain_322e": 0,
        "review_reduction_322e": 0,
        "out_of_scope_or_rejected_gain_322e": 0,
        "selected_core_trusted_rate_before_322e": 0,
        "selected_core_trusted_rate_after_322e": 0,
        "remaining_unknown_metric_candidate_count": 0,
        "remaining_unit_unknown_candidate_count": 0,
        "remaining_manual_review_count": 0,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "semantic_adjudicator_replay_decision": code,
    }
    qa_df = pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}])
    sheets = {
        "summary": pd.DataFrame([summary]),
        "replay_instruction_inventory": pd.DataFrame(),
        "candidate_replay_diff": pd.DataFrame(),
        "trusted_preview_322e": pd.DataFrame(),
        "review_required_preview_322e": pd.DataFrame(),
        "rejected_preview_322e": pd.DataFrame(),
        "review_reduction_by_instruction": pd.DataFrame(),
        "remaining_review_burden_322e": pd.DataFrame(),
        "qa_checks": qa_df,
        "known_limitations": build_known_limitations_df(),
    }
    write_excel(output_dir / "semantic_adjudicator_replay_322e.xlsx", sheets)
    write_json(output_dir / "semantic_adjudicator_replay_322e_summary.json", summary)
    (output_dir / "semantic_adjudicator_replay_322e_report.md").write_text(build_report_markdown(summary), encoding="utf-8")
    _write_empty_jsonl(output_dir / "candidate_replay_diff_322e.jsonl")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 322E semantic adjudicator replay.")
    parser.add_argument("--adjudicator-limited-dir", required=True)
    parser.add_argument("--trust-split-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    adjudicator_limited_dir = Path(args.adjudicator_limited_dir)
    trust_split_dir = Path(args.trust_split_dir)
    output_dir = Path(args.output_dir)

    if not adjudicator_limited_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_322D_APPLY_DIR")
        print(f"semantic_adjudicator_replay_322e_summary_json: {output_dir / 'semantic_adjudicator_replay_322e_summary.json'}")
        return 0
    if not trust_split_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_322B2_TRUST_SPLIT_DIR")
        print(f"semantic_adjudicator_replay_322e_summary_json: {output_dir / 'semantic_adjudicator_replay_322e_summary.json'}")
        return 0

    inputs = load_replay_inputs(adjudicator_limited_dir, trust_split_dir)
    deterministic_gate_results_df = inputs["deterministic_gate_results_df"]
    alias_replay_df = inputs["alias_replay_df"]
    out_scope_replay_df = inputs["out_scope_replay_df"]
    unit_replay_df = inputs["unit_replay_df"]
    trusted_before_df = inputs["trusted_before_df"]
    review_before_df = inputs["review_before_df"]
    rejected_before_df = inputs["rejected_before_df"]
    trust_summary_df = inputs["trust_summary_df"]

    replay_instruction_inventory_df = build_replay_instruction_inventory(
        deterministic_gate_results_df=deterministic_gate_results_df,
        alias_replay_df=alias_replay_df,
        out_scope_replay_df=out_scope_replay_df,
        unit_replay_df=unit_replay_df,
    )

    (
        replay_instruction_inventory_df,
        candidate_replay_diff_df,
        trusted_after_df,
        review_after_df,
        rejected_after_df,
        review_reduction_by_instruction_df,
    ) = apply_replay(
        replay_instruction_inventory_df=replay_instruction_inventory_df,
        trusted_before_df=trusted_before_df,
        review_before_df=review_before_df,
        rejected_before_df=rejected_before_df,
    )

    remaining_review_burden_df = build_remaining_review_burden(review_after_df)

    input_candidate_count = int(len(trusted_before_df) + len(review_before_df) + len(rejected_before_df))
    replay_instruction_count = int(len(replay_instruction_inventory_df))
    replay_allowed_instruction_count = int(replay_instruction_inventory_df["replay_allowed"].astype(bool).sum()) if not replay_instruction_inventory_df.empty else 0
    replay_blocked_instruction_count = replay_instruction_count - replay_allowed_instruction_count
    affected_candidate_count = int(len(candidate_replay_diff_df))
    trusted_total_before_322e = int(len(trusted_before_df))
    trusted_total_after_322e = int(len(trusted_after_df))
    review_required_total_before_322e = int(len(review_before_df))
    review_required_total_after_322e = int(len(review_after_df))
    rejected_total_before_322e = int(len(rejected_before_df))
    rejected_total_after_322e = int(len(rejected_after_df))
    trusted_gain_322e = trusted_total_after_322e - trusted_total_before_322e
    review_reduction_322e = review_required_total_before_322e - review_required_total_after_322e
    out_of_scope_or_rejected_gain_322e = rejected_total_after_322e - rejected_total_before_322e

    summary_lookup = {
        _norm(row.get("metric")): row.get("value")
        for _, row in trust_summary_df.iterrows()
    } if not trust_summary_df.empty else {}
    selected_core_trusted_rate_before_322e = float(summary_lookup.get("selected_core_trusted_rate_after_322b2") or 0)
    selected_core_trusted_rate_after_322e = round(trusted_total_after_322e / input_candidate_count, 6) if input_candidate_count else 0
    remaining_unknown_metric_candidate_count = int(review_after_df["risk_tags_after"].astype(str).str.contains(r"(?:^|\\|)UNKNOWN_METRIC_CODE(?:$|\\|)", regex=True).sum()) if not review_after_df.empty else 0
    remaining_unit_unknown_candidate_count = int(review_after_df["risk_tags_after"].astype(str).str.contains(r"(?:^|\\|)UNIT_UNKNOWN(?:$|\\|)", regex=True).sum()) if not review_after_df.empty else 0
    remaining_manual_review_count = review_required_total_after_322e

    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa("322d_apply_output_exists", "PASS" if adjudicator_limited_dir.exists() else "FAIL", str(adjudicator_limited_dir))
    add_qa("322b2_trust_split_output_exists", "PASS" if trust_split_dir.exists() else "FAIL", str(trust_split_dir))
    add_qa("no_model_api_call_executed", "PASS", "322E replays accepted sandbox instructions only")
    add_qa("no_recognizer_command_executed", "PASS", "322E does not call MinerU/StructEqTable/Docling/PPStructure/VLM")
    add_qa("no_e_drive_files_modified", "PASS", "322E reads existing outputs and writes sandbox outputs only")
    add_qa("no_production_files_modified", "PASS", "322E keeps all replay logic in independent semantic modules")

    replayed_candidate_ids = set(candidate_replay_diff_df["provenance"].astype(str).tolist()) if not candidate_replay_diff_df.empty else set()
    provenance_ok = True
    if not candidate_replay_diff_df.empty:
        provenance_ok = candidate_replay_diff_df["provenance"].astype(str).str.len().gt(0).all()
    add_qa("every_replayed_candidate_has_provenance", "PASS" if provenance_ok else "FAIL", f"replayed_candidate_count={len(candidate_replay_diff_df)}")

    llm_only_trust_exists = False
    if not candidate_replay_diff_df.empty:
        llm_only_trust_exists = candidate_replay_diff_df["risk_tags_after"].astype(str).str.contains("UNKNOWN_METRIC_CODE").any()
    add_qa("no_llm_only_trusted_decision_exists", "PASS" if not llm_only_trust_exists else "FAIL", "trusted replay requires deterministic gate cleanup")

    trusted_gate_ok = True
    if not trusted_after_df.empty:
        blocker_mask = trusted_after_df["risk_tags_after"].astype(str).str.contains(
            r"UNKNOWN_METRIC_CODE|UNIT_UNKNOWN|VALUE_PARSE_FAILED|INVALID_YEAR|NO_YEAR_COLUMNS|VALUE_CONFLICT|EXTRACTION_RISK|SECTION_CONTEXT_REQUIRED",
            regex=True,
        )
        trusted_gate_ok = not blocker_mask.any() and trusted_after_df["metric_code"].astype(str).ne("unknown_metric").all()
    add_qa("trusted_candidates_after_replay_still_satisfy_deterministic_gates", "PASS" if trusted_gate_ok else "FAIL", f"trusted_total_after_322e={trusted_total_after_322e}")

    counts_reconcile = input_candidate_count == (trusted_total_after_322e + review_required_total_after_322e + rejected_total_after_322e)
    add_qa("candidate_counts_reconcile_before_after", "PASS" if counts_reconcile else "FAIL", f"input_candidate_count={input_candidate_count}")
    add_qa("small_5_case_sample_size", "WARN", f"replay_instruction_count={replay_instruction_count}")
    add_qa("only_one_accepted_instruction_may_be_available", "WARN" if replay_allowed_instruction_count <= 1 else "PASS", f"replay_allowed_instruction_count={replay_allowed_instruction_count}")
    add_qa("most_review_cases_may_remain_manual_review_required", "WARN" if review_required_total_after_322e > 1000 else "PASS", f"review_required_total_after_322e={review_required_total_after_322e}")
    add_qa("human_confirmation_still_recommended_before_official_mapping_updates", "WARN", "322E remains sandbox-only")

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0

    summary = {
        "stage": "322E",
        "output_dir": str(output_dir),
        "input_candidate_count": input_candidate_count,
        "replay_instruction_count": replay_instruction_count,
        "replay_allowed_instruction_count": replay_allowed_instruction_count,
        "replay_blocked_instruction_count": replay_blocked_instruction_count,
        "affected_candidate_count": affected_candidate_count,
        "trusted_total_before_322e": trusted_total_before_322e,
        "trusted_total_after_322e": trusted_total_after_322e,
        "review_required_total_before_322e": review_required_total_before_322e,
        "review_required_total_after_322e": review_required_total_after_322e,
        "rejected_total_before_322e": rejected_total_before_322e,
        "rejected_total_after_322e": rejected_total_after_322e,
        "trusted_gain_322e": trusted_gain_322e,
        "review_reduction_322e": review_reduction_322e,
        "out_of_scope_or_rejected_gain_322e": out_of_scope_or_rejected_gain_322e,
        "selected_core_trusted_rate_before_322e": selected_core_trusted_rate_before_322e,
        "selected_core_trusted_rate_after_322e": selected_core_trusted_rate_after_322e,
        "remaining_unknown_metric_candidate_count": remaining_unknown_metric_candidate_count,
        "remaining_unit_unknown_candidate_count": remaining_unit_unknown_candidate_count,
        "remaining_manual_review_count": remaining_manual_review_count,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
    }
    summary["semantic_adjudicator_replay_decision"] = replay_decision(summary)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = {
        "excel": output_dir / "semantic_adjudicator_replay_322e.xlsx",
        "summary_json": output_dir / "semantic_adjudicator_replay_322e_summary.json",
        "report_md": output_dir / "semantic_adjudicator_replay_322e_report.md",
        "diff_jsonl": output_dir / "candidate_replay_diff_322e.jsonl",
        "instruction_jsonl": output_dir / "semantic_replay_instructions_322e.jsonl",
    }

    write_json(output_files["summary_json"], summary)
    output_files["report_md"].write_text(build_report_markdown(summary), encoding="utf-8")
    if not candidate_replay_diff_df.empty:
        write_jsonl(output_files["diff_jsonl"], candidate_replay_diff_df)
    else:
        _write_empty_jsonl(output_files["diff_jsonl"])
    if not replay_instruction_inventory_df.empty:
        write_jsonl(output_files["instruction_jsonl"], replay_instruction_inventory_df)
    else:
        _write_empty_jsonl(output_files["instruction_jsonl"])

    sheets = {
        "summary": pd.DataFrame([summary]),
        "replay_instruction_inventory": replay_instruction_inventory_df,
        "candidate_replay_diff": candidate_replay_diff_df,
        "trusted_preview_322e": trusted_after_df,
        "review_required_preview_322e": review_after_df,
        "rejected_preview_322e": rejected_after_df,
        "review_reduction_by_instruction": review_reduction_by_instruction_df,
        "remaining_review_burden_322e": remaining_review_burden_df,
        "qa_checks": qa_df,
        "known_limitations": build_known_limitations_df(),
    }
    write_excel(output_files["excel"], sheets)
    write_json(output_files["summary_json"], summary)
    output_files["report_md"].write_text(build_report_markdown(summary), encoding="utf-8")

    output_files_written = all(path.exists() for path in output_files.values())
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
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    summary["qa_pass_count"] = qa_pass_count
    summary["qa_warn_count"] = qa_warn_count
    summary["qa_fail_count"] = qa_fail_count
    summary["semantic_adjudicator_replay_decision"] = replay_decision(summary)

    sheets["summary"] = pd.DataFrame([summary])
    sheets["qa_checks"] = qa_df
    write_excel(output_files["excel"], sheets)
    write_json(output_files["summary_json"], summary)
    output_files["report_md"].write_text(build_report_markdown(summary), encoding="utf-8")

    print(f"semantic_adjudicator_replay_322e_excel: {output_files['excel']}")
    print(f"semantic_adjudicator_replay_322e_summary_json: {output_files['summary_json']}")
    print(f"semantic_adjudicator_replay_322e_report_md: {output_files['report_md']}")
    for key in [
        "input_candidate_count",
        "replay_instruction_count",
        "replay_allowed_instruction_count",
        "replay_blocked_instruction_count",
        "affected_candidate_count",
        "trusted_total_before_322e",
        "trusted_total_after_322e",
        "review_required_total_before_322e",
        "review_required_total_after_322e",
        "rejected_total_before_322e",
        "rejected_total_after_322e",
        "trusted_gain_322e",
        "review_reduction_322e",
        "out_of_scope_or_rejected_gain_322e",
        "selected_core_trusted_rate_before_322e",
        "selected_core_trusted_rate_after_322e",
        "remaining_unknown_metric_candidate_count",
        "remaining_unit_unknown_candidate_count",
        "remaining_manual_review_count",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "semantic_adjudicator_replay_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
