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

from datefac.semantic.alias_safe_adjudicator_request_325e import (  # noqa: E402
    DEFAULT_ALIAS_REVIEW_BATCH_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_DIR,
    DEFAULT_SANITY_GATE_DIR,
    NOT_READY_DECISION,
    build_alias_safe_adjudicator_request_325e,
    load_alias_safe_adjudicator_request_325e_inputs,
)
from datefac.semantic.alias_safe_adjudicator_request_325e_report import (  # noqa: E402
    alias_safe_adjudicator_request_325e_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "325E",
        "output_dir": str(output_dir),
        "request_count": 0,
        "alias_request_count": 0,
        "excluded_holdout_count": 0,
        "excluded_rejected_count": 0,
        "excluded_needs_more_info_count": 0,
        "excluded_pending_count": 0,
        "llm_or_adjudicator_called": False,
        "official_assets_modified": False,
        "official_assets_written": [],
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
    write_json(output_dir / "alias_safe_adjudicator_request_325e_summary.json", summary)
    write_json(output_dir / "alias_safe_adjudicator_request_325e_qa.json", qa_json)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 325E alias safe adjudicator request prep.")
    parser.add_argument("--reviewed-dir", default=str(DEFAULT_REVIEWED_DIR))
    parser.add_argument("--sanity-gate-dir", default=str(DEFAULT_SANITY_GATE_DIR))
    parser.add_argument("--alias-review-batch-dir", default=str(DEFAULT_ALIAS_REVIEW_BATCH_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    reviewed_dir = Path(args.reviewed_dir)
    sanity_gate_dir = Path(args.sanity_gate_dir)
    alias_review_batch_dir = Path(args.alias_review_batch_dir)
    output_dir = Path(args.output_dir)

    required_files = [
        (reviewed_dir / "alias_human_spot_check_325d_reviewed_summary.json", "BLOCKED_MISSING_325D_REVIEWED_SUMMARY"),
        (reviewed_dir / "alias_human_spot_check_325d_reviewed_qa.json", "BLOCKED_MISSING_325D_REVIEWED_QA"),
        (reviewed_dir / "alias_human_spot_check_325d_final_routing_plan.json", "BLOCKED_MISSING_325D_FINAL_ROUTING_PLAN"),
        (sanity_gate_dir / "alias_review_batch_sanity_gate_325c_summary.json", "BLOCKED_MISSING_325C_SUMMARY"),
        (alias_review_batch_dir / "alias_review_batch_325b_summary.json", "BLOCKED_MISSING_325B_SUMMARY"),
    ]
    for path, code in required_files:
        if not path.exists():
            summary = _blocked_result(output_dir, code)
            print(f"qa_fail_count: {summary.get('qa_fail_count', '')}")
            print(f"decision: {summary.get('decision', '')}")
            return 0

    inputs = load_alias_safe_adjudicator_request_325e_inputs(
        reviewed_dir=reviewed_dir,
        sanity_gate_dir=sanity_gate_dir,
        alias_review_batch_dir=alias_review_batch_dir,
    )
    artifacts = build_alias_safe_adjudicator_request_325e(
        summary_325d=inputs["summary_325d"],
        qa_325d=inputs["qa_325d"],
        final_routing_plan=inputs["final_routing_plan"],
        official_asset_hashes_before=inputs["official_asset_hashes_before"],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    write_json(output_dir / "alias_safe_adjudicator_request_325e_summary.json", summary)
    write_json(output_dir / "alias_safe_adjudicator_request_325e_qa.json", artifacts["qa_json"])
    write_json(output_dir / "alias_safe_adjudicator_request_325e_request_package.json", artifacts["request_package"])
    write_json(output_dir / "alias_safe_adjudicator_request_325e_schema.json", artifacts["response_schema"])
    write_json(output_dir / "alias_safe_adjudicator_request_325e_no_apply_proof.json", artifacts["no_apply_proof"])
    write_jsonl(output_dir / "alias_safe_adjudicator_request_325e_request_items.jsonl", artifacts["request_items"])
    write_excel(
        output_dir / "alias_safe_adjudicator_request_325e_evidence_workbook.xlsx",
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "request_items": artifacts["request_items_df"],
            "excluded_items": artifacts["excluded_items_df"],
            "response_schema": artifacts["schema_df"],
            "qa_checks": artifacts["qa_checks_df"],
        },
    )
    write_excel(
        output_dir / "alias_safe_adjudicator_request_325e_excluded_items.xlsx",
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "excluded_items": artifacts["excluded_items_df"],
            "request_items": pd.DataFrame(),
            "response_schema": artifacts["schema_df"],
            "qa_checks": artifacts["qa_checks_df"],
        },
    )
    (output_dir / "alias_safe_adjudicator_request_325e_manual_prompt.md").write_text(
        alias_safe_adjudicator_request_325e_markdown(summary, artifacts["response_schema"]),
        encoding="utf-8",
    )

    print(f"output_dir: {output_dir}")
    for key in [
        "request_count",
        "alias_request_count",
        "excluded_holdout_count",
        "excluded_rejected_count",
        "excluded_needs_more_info_count",
        "excluded_pending_count",
        "llm_or_adjudicator_called",
        "official_assets_modified",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
