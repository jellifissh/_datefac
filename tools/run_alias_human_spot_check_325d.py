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

from datefac.semantic.alias_human_spot_check_325d import (  # noqa: E402
    DEFAULT_ALIAS_REVIEW_BATCH_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_OUTPUT_DIR,
    DEFAULT_SANITY_GATE_DIR,
    NOT_READY_DECISION,
    build_alias_human_spot_check_325d_prepare,
    build_alias_human_spot_check_325d_reviewed,
    load_alias_human_spot_check_325d_inputs,
    load_reviewed_workbook_records,
)
from datefac.semantic.alias_human_spot_check_325d_report import (  # noqa: E402
    alias_human_spot_check_325d_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, mode: str, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "325D",
        "mode": mode,
        "output_dir": str(output_dir),
        "spot_check_record_count": 0,
        "pending_count": 0,
        "send_to_adjudicator_count": 0,
        "holdout_count": 0,
        "rejected_count": 0,
        "needs_more_info_count": 0,
        "carried_forward_325c_holdout_count": 0,
        "validate_reviewed_mode_implemented": True,
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
    prefix = "alias_human_spot_check_325d_reviewed" if mode == "validate-reviewed" else "alias_human_spot_check_325d"
    write_json(output_dir / f"{prefix}_summary.json", summary)
    write_json(output_dir / f"{prefix}_qa.json", qa_json)
    (output_dir / f"{prefix}_review_instructions.md").write_text(alias_human_spot_check_325d_markdown(summary), encoding="utf-8")
    return summary


def _write_prepare_outputs(output_dir: Path, artifacts: Dict[str, Any]) -> None:
    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    write_json(output_dir / "alias_human_spot_check_325d_summary.json", summary)
    write_json(output_dir / "alias_human_spot_check_325d_qa.json", artifacts["qa_json"])
    write_json(output_dir / "alias_human_spot_check_325d_review_package.json", artifacts["review_package"])
    write_json(output_dir / "alias_human_spot_check_325d_no_apply_proof.json", artifacts["no_apply_proof"])
    write_excel(
        output_dir / "alias_human_spot_check_325d_workbook.xlsx",
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "spot_check_records": artifacts["spot_check_df"],
            "carried_forward_holdout": artifacts["holdout_df"],
            "send_to_adjudicator": pd.DataFrame(),
            "holdout_or_rejected": pd.DataFrame(),
            "qa_checks": artifacts["qa_checks_df"],
        },
    )
    (output_dir / "alias_human_spot_check_325d_review_instructions.md").write_text(
        alias_human_spot_check_325d_markdown(summary),
        encoding="utf-8",
    )


def _write_reviewed_outputs(output_dir: Path, artifacts: Dict[str, Any]) -> None:
    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    write_json(output_dir / "alias_human_spot_check_325d_reviewed_summary.json", summary)
    write_json(output_dir / "alias_human_spot_check_325d_reviewed_qa.json", artifacts["qa_json"])
    write_json(output_dir / "alias_human_spot_check_325d_final_routing_plan.json", artifacts["final_routing_plan"])
    write_json(output_dir / "alias_human_spot_check_325d_no_apply_proof.json", artifacts["no_apply_proof"])
    write_excel(
        output_dir / "alias_human_spot_check_325d_reviewed_workbook.xlsx",
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "spot_check_records": artifacts["reviewed_df"],
            "carried_forward_holdout": artifacts["carried_forward_holdout_df"],
            "send_to_adjudicator": artifacts["send_to_adjudicator_df"],
            "holdout_or_rejected": artifacts["holdout_or_rejected_df"],
            "qa_checks": artifacts["qa_checks_df"],
        },
    )
    write_excel(
        output_dir / "alias_human_spot_check_325d_send_to_adjudicator.xlsx",
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "send_to_adjudicator": artifacts["send_to_adjudicator_df"],
            "spot_check_records": pd.DataFrame(),
            "carried_forward_holdout": pd.DataFrame(),
            "holdout_or_rejected": pd.DataFrame(),
            "qa_checks": artifacts["qa_checks_df"],
        },
    )
    write_excel(
        output_dir / "alias_human_spot_check_325d_holdout_or_rejected.xlsx",
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "holdout_or_rejected": artifacts["holdout_or_rejected_df"],
            "spot_check_records": pd.DataFrame(),
            "carried_forward_holdout": artifacts["carried_forward_holdout_df"],
            "send_to_adjudicator": pd.DataFrame(),
            "qa_checks": artifacts["qa_checks_df"],
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 325D alias human spot-check workflow.")
    parser.add_argument("--mode", choices=["prepare", "validate-reviewed"], default="prepare")
    parser.add_argument("--sanity-gate-dir", default=str(DEFAULT_SANITY_GATE_DIR))
    parser.add_argument("--alias-review-batch-dir", default=str(DEFAULT_ALIAS_REVIEW_BATCH_DIR))
    parser.add_argument("--reviewed-workbook", default="")
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args()

    mode = args.mode
    sanity_gate_dir = Path(args.sanity_gate_dir)
    alias_review_batch_dir = Path(args.alias_review_batch_dir)
    output_dir = Path(args.output_dir) if args.output_dir else (DEFAULT_REVIEWED_OUTPUT_DIR if mode == "validate-reviewed" else DEFAULT_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    required_files = [
        (sanity_gate_dir / "alias_review_batch_sanity_gate_325c_summary.json", "BLOCKED_MISSING_325C_SUMMARY"),
        (sanity_gate_dir / "alias_review_batch_sanity_gate_325c_qa.json", "BLOCKED_MISSING_325C_QA"),
        (sanity_gate_dir / "alias_review_batch_sanity_gate_325c_routing_manifest.json", "BLOCKED_MISSING_325C_ROUTING_MANIFEST"),
        (alias_review_batch_dir / "alias_review_batch_325b_summary.json", "BLOCKED_MISSING_325B_SUMMARY"),
    ]
    if mode == "validate-reviewed":
        reviewed_workbook = Path(args.reviewed_workbook)
        required_files.append((reviewed_workbook, "BLOCKED_MISSING_REVIEWED_WORKBOOK"))
    else:
        reviewed_workbook = Path()

    for path, code in required_files:
        if not path.exists():
            summary = _blocked_result(output_dir, mode, code)
            print(f"qa_fail_count: {summary.get('qa_fail_count', '')}")
            print(f"decision: {summary.get('decision', '')}")
            return 0

    inputs = load_alias_human_spot_check_325d_inputs(sanity_gate_dir, alias_review_batch_dir)
    if mode == "prepare":
        artifacts = build_alias_human_spot_check_325d_prepare(
            summary_325c=inputs["summary_325c"],
            qa_325c=inputs["qa_325c"],
            routing_records=inputs["routing_records"],
            official_asset_hashes_before=inputs["official_asset_hashes_before"],
        )
        _write_prepare_outputs(output_dir, artifacts)
    else:
        artifacts = build_alias_human_spot_check_325d_reviewed(
            summary_325c=inputs["summary_325c"],
            qa_325c=inputs["qa_325c"],
            routing_records=inputs["routing_records"],
            reviewed_records=load_reviewed_workbook_records(reviewed_workbook),
            official_asset_hashes_before=inputs["official_asset_hashes_before"],
        )
        _write_reviewed_outputs(output_dir, artifacts)

    summary = artifacts["summary"]
    print(f"output_dir: {output_dir}")
    for key in [
        "mode",
        "spot_check_record_count",
        "pending_count",
        "send_to_adjudicator_count",
        "holdout_count",
        "rejected_count",
        "needs_more_info_count",
        "invalid_decision_count",
        "carried_forward_325c_holdout_count",
        "validate_reviewed_mode_implemented",
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
