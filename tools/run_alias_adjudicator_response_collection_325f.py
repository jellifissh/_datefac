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

from datefac.semantic.alias_adjudicator_response_collection_325f import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REQUEST_DIR,
    EXPECTED_325F_NOT_READY,
    build_alias_adjudicator_response_collection_325f_collect_manual,
    build_alias_adjudicator_response_collection_325f_prepare_manual,
    load_alias_adjudicator_response_collection_325f_inputs,
)
from datefac.semantic.alias_adjudicator_response_collection_325f_report import (  # noqa: E402
    alias_adjudicator_response_collection_325f_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def _blocked_result(output_dir: Path, mode: str, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "325F",
        "mode": mode,
        "output_dir": str(output_dir),
        "request_count": 0,
        "raw_response_count": 0,
        "response_received_count": 0,
        "collect_manual_mode_implemented": True,
        "llm_or_adjudicator_called": False,
        "official_assets_modified": False,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_325F_NOT_READY,
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
        "request_response_items": pd.DataFrame(),
        "manual_response_template": pd.DataFrame(),
        "qa_checks": pd.DataFrame(qa_json["checks"]),
    }
    write_json(output_dir / "alias_adjudicator_response_collection_325f_summary.json", summary)
    write_json(output_dir / "alias_adjudicator_response_collection_325f_qa.json", qa_json)
    write_json(output_dir / "alias_adjudicator_response_collection_325f_response_manifest.json", {"raw_response_count": 0})
    write_json(output_dir / "alias_adjudicator_response_collection_325f_run_metadata.json", {"mode": mode, "decision": "blocked_input"})
    write_json(output_dir / "alias_adjudicator_response_collection_325f_no_apply_proof.json", {"decision": "blocked_input"})
    write_jsonl(output_dir / "alias_adjudicator_response_collection_325f_raw_responses.jsonl", [])
    write_excel(output_dir / "alias_adjudicator_response_collection_325f_request_response_workbook.xlsx", sheets)
    write_excel(output_dir / "alias_adjudicator_response_collection_325f_manual_response_template.xlsx", sheets)
    (output_dir / "alias_adjudicator_response_collection_325f_notes.md").write_text(
        alias_adjudicator_response_collection_325f_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 325F alias adjudicator raw response collection.")
    parser.add_argument("--mode", choices=["prepare-manual", "collect-manual"], default="prepare-manual")
    parser.add_argument("--request-dir", default=str(DEFAULT_REQUEST_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--manual-response-workbook", default="")
    args = parser.parse_args()

    request_dir = Path(args.request_dir)
    output_dir = Path(args.output_dir)
    manual_response_workbook = Path(args.manual_response_workbook) if args.manual_response_workbook else (
        output_dir / "alias_adjudicator_response_collection_325f_manual_response_template.xlsx"
    )

    required_paths = [
        request_dir / "alias_safe_adjudicator_request_325e_summary.json",
        request_dir / "alias_safe_adjudicator_request_325e_qa.json",
        request_dir / "alias_safe_adjudicator_request_325e_request_package.json",
    ]
    if not all(path.exists() for path in required_paths):
        summary = _blocked_result(output_dir, args.mode, "BLOCKED_MISSING_325E_REQUEST_ARTIFACTS")
        print(f"qa_fail_count: {summary.get('qa_fail_count', '')}")
        print(f"decision: {summary.get('decision', '')}")
        return 0
    if args.mode == "collect-manual" and not manual_response_workbook.exists():
        summary = _blocked_result(output_dir, args.mode, "BLOCKED_MISSING_MANUAL_RESPONSE_WORKBOOK")
        print(f"qa_fail_count: {summary.get('qa_fail_count', '')}")
        print(f"decision: {summary.get('decision', '')}")
        return 0

    inputs = load_alias_adjudicator_response_collection_325f_inputs(request_dir)
    if args.mode == "prepare-manual":
        artifacts = build_alias_adjudicator_response_collection_325f_prepare_manual(inputs, request_dir)
    else:
        artifacts = build_alias_adjudicator_response_collection_325f_collect_manual(
            inputs,
            request_dir,
            manual_response_workbook,
        )

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "summary": output_dir / "alias_adjudicator_response_collection_325f_summary.json",
        "qa": output_dir / "alias_adjudicator_response_collection_325f_qa.json",
        "raw": output_dir / "alias_adjudicator_response_collection_325f_raw_responses.jsonl",
        "manifest": output_dir / "alias_adjudicator_response_collection_325f_response_manifest.json",
        "workbook": output_dir / "alias_adjudicator_response_collection_325f_request_response_workbook.xlsx",
        "metadata": output_dir / "alias_adjudicator_response_collection_325f_run_metadata.json",
        "manual_template": output_dir / "alias_adjudicator_response_collection_325f_manual_response_template.xlsx",
        "notes": output_dir / "alias_adjudicator_response_collection_325f_notes.md",
        "no_apply": output_dir / "alias_adjudicator_response_collection_325f_no_apply_proof.json",
    }
    sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "request_response_items": artifacts["request_response_df"],
        "manual_response_template": artifacts["manual_template_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }
    write_json(paths["summary"], summary)
    write_json(paths["qa"], artifacts["qa_json"])
    write_json(paths["manifest"], artifacts["response_manifest_json"])
    write_json(paths["metadata"], artifacts["run_metadata_json"])
    write_json(paths["no_apply"], artifacts["no_apply_proof_json"])
    write_jsonl(paths["raw"], artifacts["raw_responses"])
    write_excel(paths["workbook"], sheets)
    write_excel(paths["manual_template"], sheets)
    paths["notes"].write_text(alias_adjudicator_response_collection_325f_markdown(summary), encoding="utf-8")

    print(f"output_dir: {output_dir}")
    for key in [
        "mode",
        "request_count",
        "raw_response_count",
        "response_received_count",
        "collect_manual_mode_implemented",
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
