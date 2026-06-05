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

from datefac.semantic.alias_review_batch_sanity_gate_325c import (  # noqa: E402
    DEFAULT_ALIAS_REFINEMENT_DIR,
    DEFAULT_ALIAS_REVIEW_BATCH_DIR,
    DEFAULT_OUTPUT_DIR,
    FORMAL_SCOPE_RULES_PATH,
    NOT_READY_DECISION,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_alias_review_batch_sanity_gate_325c,
    load_alias_review_batch_sanity_gate_325c_inputs,
)
from datefac.semantic.alias_review_batch_sanity_gate_325c_report import (  # noqa: E402
    alias_review_batch_sanity_gate_325c_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "325C",
        "output_dir": str(output_dir),
        "input_review_record_count": 0,
        "routing_bucket_counts": {},
        "send_to_adjudicator_count": 0,
        "human_spot_check_count": 0,
        "holdout_count": 0,
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
    write_json(output_dir / "alias_review_batch_sanity_gate_325c_summary.json", summary)
    write_json(output_dir / "alias_review_batch_sanity_gate_325c_qa.json", qa_json)
    write_json(
        output_dir / "alias_review_batch_sanity_gate_325c_routing_manifest.json",
        {"stage": "325C", "decision": NOT_READY_DECISION, "routing_records": []},
    )
    write_excel(
        output_dir / "alias_review_batch_sanity_gate_325c_routing_manifest.xlsx",
        {
            "summary": pd.DataFrame([summary]),
            "routing_manifest": pd.DataFrame(),
            "send_to_adjudicator": pd.DataFrame(),
            "human_spot_check": pd.DataFrame(),
            "holdout": pd.DataFrame(),
            "routing_bucket_summary": pd.DataFrame(),
            "qa_checks": pd.DataFrame(qa_json["checks"]),
        },
    )
    write_json(output_dir / "alias_review_batch_sanity_gate_325c_no_apply_proof.json", summary)
    (output_dir / "alias_review_batch_sanity_gate_325c_notes.md").write_text(
        alias_review_batch_sanity_gate_325c_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 325C alias review batch sanity gate.")
    parser.add_argument("--alias-review-batch-dir", default=str(DEFAULT_ALIAS_REVIEW_BATCH_DIR))
    parser.add_argument("--alias-refinement-dir", default=str(DEFAULT_ALIAS_REFINEMENT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    alias_review_batch_dir = Path(args.alias_review_batch_dir)
    alias_refinement_dir = Path(args.alias_refinement_dir)
    output_dir = Path(args.output_dir)

    required_files = [
        (alias_review_batch_dir / "alias_review_batch_325b_summary.json", "BLOCKED_MISSING_325B_SUMMARY"),
        (alias_review_batch_dir / "alias_review_batch_325b_qa.json", "BLOCKED_MISSING_325B_QA"),
        (alias_review_batch_dir / "alias_review_batch_325b_review_package.json", "BLOCKED_MISSING_325B_REVIEW_PACKAGE"),
        (alias_refinement_dir / "alias_candidate_refinement_325a_summary.json", "BLOCKED_MISSING_325A_SUMMARY"),
        (alias_refinement_dir / "alias_candidate_refinement_325a_refined_alias_candidates.json", "BLOCKED_MISSING_325A_REFINED_JSON"),
        (FORMAL_SCOPE_RULES_PATH, "BLOCKED_MISSING_FORMAL_SCOPE_RULES"),
        (SEMANTIC_ALIAS_ASSET_PATH, "BLOCKED_MISSING_SEMANTIC_ALIAS_ASSET"),
    ]
    for path, code in required_files:
        if not path.exists():
            summary = _blocked_result(output_dir, code)
            print(f"alias_review_batch_sanity_gate_325c_summary_json: {output_dir / 'alias_review_batch_sanity_gate_325c_summary.json'}")
            print(f"qa_fail_count: {summary.get('qa_fail_count', '')}")
            print(f"decision: {summary.get('decision', '')}")
            return 0

    inputs = load_alias_review_batch_sanity_gate_325c_inputs(alias_review_batch_dir, alias_refinement_dir)
    artifacts = build_alias_review_batch_sanity_gate_325c(
        summary_325b=inputs["summary_325b"],
        qa_325b=inputs["qa_325b"],
        review_records=inputs["review_records"],
        summary_325a=inputs["summary_325a"],
        refined_325a=inputs["refined_325a"],
        formal_scope_rules=inputs["formal_scope_rules"],
        semantic_alias_asset=inputs["semantic_alias_asset"],
        official_asset_hashes_before=inputs["official_asset_hashes_before"],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = {
        "summary_json": output_dir / "alias_review_batch_sanity_gate_325c_summary.json",
        "qa_json": output_dir / "alias_review_batch_sanity_gate_325c_qa.json",
        "routing_manifest_json": output_dir / "alias_review_batch_sanity_gate_325c_routing_manifest.json",
        "routing_manifest_xlsx": output_dir / "alias_review_batch_sanity_gate_325c_routing_manifest.xlsx",
        "send_to_adjudicator_jsonl": output_dir / "alias_review_batch_sanity_gate_325c_send_to_adjudicator.jsonl",
        "human_spot_check_xlsx": output_dir / "alias_review_batch_sanity_gate_325c_human_spot_check.xlsx",
        "holdout_xlsx": output_dir / "alias_review_batch_sanity_gate_325c_holdout.xlsx",
        "notes_md": output_dir / "alias_review_batch_sanity_gate_325c_notes.md",
        "no_apply_proof_json": output_dir / "alias_review_batch_sanity_gate_325c_no_apply_proof.json",
    }

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    write_json(output_files["summary_json"], summary)
    write_json(output_files["qa_json"], artifacts["qa_json"])
    write_json(output_files["routing_manifest_json"], artifacts["routing_manifest"])
    write_json(output_files["no_apply_proof_json"], artifacts["no_apply_proof"])
    write_jsonl(
        output_files["send_to_adjudicator_jsonl"],
        artifacts["send_to_adjudicator_df"].to_dict(orient="records"),
    )
    write_excel(
        output_files["routing_manifest_xlsx"],
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "routing_manifest": artifacts["routing_manifest_df"],
            "send_to_adjudicator": artifacts["send_to_adjudicator_df"],
            "human_spot_check": artifacts["human_spot_check_df"],
            "holdout": artifacts["holdout_df"],
            "routing_bucket_summary": artifacts["routing_bucket_summary_df"],
            "qa_checks": artifacts["qa_checks_df"],
        },
    )
    write_excel(
        output_files["human_spot_check_xlsx"],
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "human_spot_check": artifacts["human_spot_check_df"],
            "routing_manifest": pd.DataFrame(),
            "send_to_adjudicator": pd.DataFrame(),
            "holdout": pd.DataFrame(),
            "routing_bucket_summary": artifacts["routing_bucket_summary_df"],
            "qa_checks": artifacts["qa_checks_df"],
        },
    )
    write_excel(
        output_files["holdout_xlsx"],
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "holdout": artifacts["holdout_df"],
            "routing_manifest": pd.DataFrame(),
            "send_to_adjudicator": pd.DataFrame(),
            "human_spot_check": pd.DataFrame(),
            "routing_bucket_summary": artifacts["routing_bucket_summary_df"],
            "qa_checks": artifacts["qa_checks_df"],
        },
    )
    output_files["notes_md"].write_text(alias_review_batch_sanity_gate_325c_markdown(summary), encoding="utf-8")

    print(f"alias_review_batch_sanity_gate_325c_summary_json: {output_files['summary_json']}")
    print(f"alias_review_batch_sanity_gate_325c_qa_json: {output_files['qa_json']}")
    print(f"alias_review_batch_sanity_gate_325c_routing_manifest_json: {output_files['routing_manifest_json']}")
    print(f"alias_review_batch_sanity_gate_325c_routing_manifest_xlsx: {output_files['routing_manifest_xlsx']}")
    print(f"alias_review_batch_sanity_gate_325c_send_to_adjudicator_jsonl: {output_files['send_to_adjudicator_jsonl']}")
    print(f"alias_review_batch_sanity_gate_325c_human_spot_check_xlsx: {output_files['human_spot_check_xlsx']}")
    print(f"alias_review_batch_sanity_gate_325c_holdout_xlsx: {output_files['holdout_xlsx']}")
    print(f"alias_review_batch_sanity_gate_325c_notes_md: {output_files['notes_md']}")
    print(f"alias_review_batch_sanity_gate_325c_no_apply_proof_json: {output_files['no_apply_proof_json']}")
    for key in [
        "input_review_record_count",
        "routing_bucket_counts",
        "send_to_adjudicator_count",
        "human_spot_check_count",
        "holdout_count",
        "already_official_count",
        "official_scope_conflict_count",
        "invalid_text_count",
        "price_or_ratio_ambiguity_count",
        "target_ambiguity_count",
        "duplicate_or_conflict_count",
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
