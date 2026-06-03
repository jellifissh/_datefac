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

from datefac.semantic.adjudication_batch_human_spot_check import (
    DEFAULT_323C_DIR,
    DEFAULT_OUTPUT_DIR,
    EXPECTED_323C_PREPARE_DECISION,
    EXPECTED_323C_PREPARE_NOT_READY,
    EXPECTED_323C_REVIEWED_DECISION,
    EXPECTED_323C_REVIEWED_NOT_READY,
    build_adjudication_batch_human_spot_check_prepare,
    build_adjudication_batch_human_spot_check_validate_reviewed,
    load_adjudication_batch_human_spot_check_inputs,
)
from datefac.semantic.adjudication_batch_human_spot_check_report import (
    adjudication_batch_human_spot_check_report_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, mode: str, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "323C-human-spot-check",
        "mode": mode,
        "output_dir": str(output_dir),
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_323C_PREPARE_NOT_READY if mode == "prepare" else EXPECTED_323C_REVIEWED_NOT_READY,
    }
    qa_json = {
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}],
    }
    sheets = {
        "summary": pd.DataFrame([summary]),
        "human_spot_check_items": pd.DataFrame(),
        "auto_send_reference": pd.DataFrame(),
        "auto_holdout_reference": pd.DataFrame(),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
        "review_instructions": pd.DataFrame([{"section": "blocked_input", "instruction": "Required input is missing."}]),
    }
    if mode == "validate-reviewed":
        sheets = {
            "summary": pd.DataFrame([summary]),
            "routing_manifest": pd.DataFrame(),
            "final_send_to_adjudicator": pd.DataFrame(),
            "final_holdouts": pd.DataFrame(),
            "reclassified_scope_candidate": pd.DataFrame(),
            "reclassified_alias_candidate": pd.DataFrame(),
            "needs_more_info": pd.DataFrame(),
            "reviewed_human_items": pd.DataFrame(),
            "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
        }

    write_json(output_dir / f"adjudication_batch_human_spot_check_323c_{mode}_summary.json", summary)
    write_json(output_dir / f"adjudication_batch_human_spot_check_323c_{mode}_qa.json", qa_json)
    write_json(output_dir / f"adjudication_batch_human_spot_check_323c_{mode}_no_apply_proof.json", {"decision": "blocked_input"})
    write_excel(
        output_dir / f"adjudication_batch_human_spot_check_323c_{mode}_package.xlsx",
        sheets,
        mode=mode,
    )
    (output_dir / f"adjudication_batch_human_spot_check_323c_{mode}_report.md").write_text(
        adjudication_batch_human_spot_check_report_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 323C human spot-check prepare/validate workflow.")
    parser.add_argument("--mode", choices=["prepare", "validate-reviewed"], default="validate-reviewed")
    parser.add_argument("--adjudication-batch-dir", default=str(DEFAULT_323C_DIR))
    parser.add_argument("--reviewed-human-workbook", default="")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    adjudication_batch_dir = Path(args.adjudication_batch_dir)
    reviewed_human_workbook = Path(args.reviewed_human_workbook) if args.reviewed_human_workbook else None
    output_dir = Path(args.output_dir)

    if not adjudication_batch_dir.exists():
        _blocked_result(output_dir, args.mode, "BLOCKED_MISSING_323C_DIR")
        print(f"adjudication_batch_human_spot_check_323c_{args.mode}_summary_json: {output_dir / f'adjudication_batch_human_spot_check_323c_{args.mode}_summary.json'}")
        return 0

    inputs = load_adjudication_batch_human_spot_check_inputs(
        adjudication_batch_dir=adjudication_batch_dir,
        reviewed_workbook=reviewed_human_workbook,
    )

    if args.mode == "prepare":
        artifacts = build_adjudication_batch_human_spot_check_prepare(
            summary_323c=inputs["summary"],
            qa_323c=inputs["qa"],
            gated_batch_items=inputs["gated_batch_items"],
        )
        summary = artifacts["summary"]
        summary["output_dir"] = str(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        workbook_path = output_dir / "adjudication_batch_human_spot_check_323c_prepare_package.xlsx"
        summary_json_path = output_dir / "adjudication_batch_human_spot_check_323c_prepare_summary.json"
        qa_json_path = output_dir / "adjudication_batch_human_spot_check_323c_prepare_qa.json"
        no_apply_path = output_dir / "adjudication_batch_human_spot_check_323c_prepare_no_apply_proof.json"
        report_path = output_dir / "adjudication_batch_human_spot_check_323c_prepare_report.md"

        sheets = {
            "summary": pd.DataFrame([summary]).fillna(""),
            "human_spot_check_items": artifacts["human_items_df"],
            "auto_send_reference": artifacts["auto_send_df"],
            "auto_holdout_reference": artifacts["auto_holdout_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "review_instructions": artifacts["review_instructions_df"],
        }

        write_json(summary_json_path, summary)
        write_json(qa_json_path, artifacts["qa_json"])
        write_json(no_apply_path, artifacts["no_apply_proof_json"])
        write_excel(workbook_path, sheets, mode="prepare")
        report_path.write_text(adjudication_batch_human_spot_check_report_markdown(summary), encoding="utf-8")

        output_files_written = all(path.exists() for path in [workbook_path, summary_json_path, qa_json_path, no_apply_path, report_path])
        qa_df = artifacts["qa_checks_df"].copy()
        qa_df = pd.concat(
            [
                qa_df,
                pd.DataFrame([{"check_name": "output_artifact_presence", "status": "PASS" if output_files_written else "FAIL", "detail": str(output_dir)}]),
            ],
            ignore_index=True,
        )
        summary["qa_pass_count"] = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
        summary["qa_warn_count"] = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
        summary["qa_fail_count"] = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
        summary["blocking_reasons"] = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []
        summary["decision"] = EXPECTED_323C_PREPARE_DECISION if summary["qa_fail_count"] == 0 else EXPECTED_323C_PREPARE_NOT_READY

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
        sheets["summary"] = pd.DataFrame([summary]).fillna("")
        sheets["qa_checks"] = qa_df
        write_excel(workbook_path, sheets, mode="prepare")
        report_path.write_text(adjudication_batch_human_spot_check_report_markdown(summary), encoding="utf-8")

        print(f"adjudication_batch_human_spot_check_323c_prepare_workbook: {workbook_path}")
        print(f"adjudication_batch_human_spot_check_323c_prepare_summary_json: {summary_json_path}")
        print(f"adjudication_batch_human_spot_check_323c_prepare_qa_json: {qa_json_path}")
        print(f"adjudication_batch_human_spot_check_323c_prepare_no_apply_proof_json: {no_apply_path}")
        print(f"adjudication_batch_human_spot_check_323c_prepare_report_md: {report_path}")
        for key in [
            "human_spot_check_item_count",
            "auto_send_count",
            "auto_holdout_count",
            "qa_pass_count",
            "qa_warn_count",
            "qa_fail_count",
            "decision",
        ]:
            print(f"{key}: {summary.get(key, '')}")
        return 0

    workbook_to_validate = reviewed_human_workbook or inputs["workbook_path"]
    if not workbook_to_validate or not workbook_to_validate.exists():
        _blocked_result(output_dir, args.mode, "BLOCKED_MISSING_REVIEWED_HUMAN_WORKBOOK")
        print(f"adjudication_batch_human_spot_check_323c_{args.mode}_summary_json: {output_dir / f'adjudication_batch_human_spot_check_323c_{args.mode}_summary.json'}")
        return 0

    artifacts = build_adjudication_batch_human_spot_check_validate_reviewed(
        summary_323c=inputs["summary"],
        qa_323c=inputs["qa"],
        gated_batch_items=inputs["gated_batch_items"],
        reviewed_items_df=inputs["human_workbook_items_df"],
        workbook_summary_df=inputs["human_workbook_summary_df"],
    )

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    workbook_path = output_dir / "adjudication_batch_human_spot_check_323c_reviewed_routing_package.xlsx"
    summary_json_path = output_dir / "adjudication_batch_human_spot_check_323c_reviewed_summary.json"
    qa_json_path = output_dir / "adjudication_batch_human_spot_check_323c_reviewed_qa.json"
    routing_plan_json_path = output_dir / "adjudication_batch_human_spot_check_323c_final_routing_plan.json"
    no_apply_path = output_dir / "adjudication_batch_human_spot_check_323c_reviewed_no_apply_proof.json"
    report_path = output_dir / "adjudication_batch_human_spot_check_323c_reviewed_report.md"

    sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "routing_manifest": artifacts["routing_manifest_df"],
        "final_send_to_adjudicator": artifacts["send_df"],
        "final_holdouts": artifacts["holdout_df"],
        "reclassified_scope_candidate": artifacts["reclassified_scope_df"],
        "reclassified_alias_candidate": artifacts["reclassified_alias_df"],
        "needs_more_info": artifacts["needs_more_info_df"],
        "reviewed_human_items": artifacts["reviewed_items_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }

    write_json(summary_json_path, summary)
    write_json(qa_json_path, artifacts["qa_json"])
    write_json(routing_plan_json_path, artifacts["routing_plan_json"])
    write_json(no_apply_path, artifacts["no_apply_proof_json"])
    write_excel(workbook_path, sheets, mode="validate-reviewed")
    report_path.write_text(adjudication_batch_human_spot_check_report_markdown(summary), encoding="utf-8")

    output_files_written = all(path.exists() for path in [workbook_path, summary_json_path, qa_json_path, routing_plan_json_path, no_apply_path, report_path])
    qa_df = artifacts["qa_checks_df"].copy()
    qa_df = pd.concat(
        [
            qa_df,
            pd.DataFrame([{"check_name": "output_artifact_presence", "status": "PASS" if output_files_written else "FAIL", "detail": str(output_dir)}]),
        ],
        ignore_index=True,
    )
    summary["qa_pass_count"] = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    summary["qa_warn_count"] = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    summary["qa_fail_count"] = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    summary["blocking_reasons"] = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []
    summary["decision"] = EXPECTED_323C_REVIEWED_DECISION if summary["qa_fail_count"] == 0 else EXPECTED_323C_REVIEWED_NOT_READY

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
    sheets["summary"] = pd.DataFrame([summary]).fillna("")
    sheets["qa_checks"] = qa_df
    write_excel(workbook_path, sheets, mode="validate-reviewed")
    report_path.write_text(adjudication_batch_human_spot_check_report_markdown(summary), encoding="utf-8")

    print(f"adjudication_batch_human_spot_check_323c_reviewed_routing_package_xlsx: {workbook_path}")
    print(f"adjudication_batch_human_spot_check_323c_reviewed_summary_json: {summary_json_path}")
    print(f"adjudication_batch_human_spot_check_323c_reviewed_qa_json: {qa_json_path}")
    print(f"adjudication_batch_human_spot_check_323c_final_routing_plan_json: {routing_plan_json_path}")
    print(f"adjudication_batch_human_spot_check_323c_reviewed_no_apply_proof_json: {no_apply_path}")
    print(f"adjudication_batch_human_spot_check_323c_reviewed_report_md: {report_path}")
    for key in [
        "reviewed_human_item_count",
        "send_to_adjudicator_count",
        "holdout_count",
        "reclassified_scope_candidate_count",
        "reclassified_alias_candidate_count",
        "needs_more_info_count",
        "pending_count",
        "invalid_decision_count",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
