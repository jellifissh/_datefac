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

from datefac.semantic.configured_adjudicator_run import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SAFE_SUBSET_DIR,
    EXPECTED_323E_MANUAL_READY,
    EXPECTED_323E_NOT_READY,
    build_configured_adjudicator_run_configured,
    build_configured_adjudicator_run_prepare_manual,
    load_configured_adjudicator_run_inputs,
)
from datefac.semantic.configured_adjudicator_run_report import (
    WORKBOOK_SHEET_ORDER,
    configured_adjudicator_run_report_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def _blocked_result(output_dir: Path, mode: str, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "323E",
        "mode": mode,
        "output_dir": str(output_dir),
        "safe_subset_dir": "",
        "request_count": 0,
        "raw_response_count": 0,
        "response_received_count": 0,
        "llm_or_adjudicator_called": False,
        "prepare_manual": mode == "prepare-manual",
        "highest_priority_examples": [],
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_323E_NOT_READY,
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
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
    }

    write_json(output_dir / "configured_adjudicator_run_323e_summary.json", summary)
    write_json(output_dir / "configured_adjudicator_run_323e_qa.json", qa_json)
    write_json(output_dir / "configured_adjudicator_run_323e_response_manifest.json", {"raw_response_count": 0})
    write_json(output_dir / "configured_adjudicator_run_323e_run_metadata.json", {"mode": mode, "decision": "blocked_input"})
    write_json(output_dir / "configured_adjudicator_run_323e_no_apply_proof.json", {"decision": "blocked_input"})
    write_jsonl(output_dir / "configured_adjudicator_run_323e_raw_responses.jsonl", [])
    write_excel(
        output_dir / "configured_adjudicator_run_323e_request_response_workbook.xlsx",
        sheets,
        WORKBOOK_SHEET_ORDER,
    )
    write_excel(
        output_dir / "configured_adjudicator_run_323e_manual_response_template.xlsx",
        sheets,
        WORKBOOK_SHEET_ORDER,
    )
    (output_dir / "configured_adjudicator_run_323e_notes.md").write_text(
        configured_adjudicator_run_report_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 323E configured adjudicator raw response collection.")
    parser.add_argument("--mode", choices=["prepare-manual", "configured-run"], default="prepare-manual")
    parser.add_argument("--safe-subset-dir", default=str(DEFAULT_SAFE_SUBSET_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--configured-raw-response-source", default="")
    args = parser.parse_args()

    safe_subset_dir = Path(args.safe_subset_dir)
    output_dir = Path(args.output_dir)
    raw_response_source = Path(args.configured_raw_response_source) if args.configured_raw_response_source else None

    if not safe_subset_dir.exists():
        _blocked_result(output_dir, args.mode, "BLOCKED_MISSING_323D_SAFE_SUBSET_DIR")
        print(f"configured_adjudicator_run_323e_summary_json: {output_dir / 'configured_adjudicator_run_323e_summary.json'}")
        return 0

    if args.mode == "configured-run" and raw_response_source is None:
        _blocked_result(output_dir, args.mode, "BLOCKED_MISSING_CONFIGURED_RAW_RESPONSE_SOURCE")
        print(f"configured_adjudicator_run_323e_summary_json: {output_dir / 'configured_adjudicator_run_323e_summary.json'}")
        return 0

    inputs = load_configured_adjudicator_run_inputs(safe_subset_dir=safe_subset_dir)

    if args.mode == "prepare-manual":
        artifacts = build_configured_adjudicator_run_prepare_manual(
            inputs=inputs,
            mode=args.mode,
            safe_subset_dir=safe_subset_dir,
        )
    else:
        artifacts = build_configured_adjudicator_run_configured(
            inputs=inputs,
            mode=args.mode,
            safe_subset_dir=safe_subset_dir,
            raw_response_source=raw_response_source or Path(""),
        )

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = output_dir / "configured_adjudicator_run_323e_summary.json"
    qa_path = output_dir / "configured_adjudicator_run_323e_qa.json"
    raw_responses_path = output_dir / "configured_adjudicator_run_323e_raw_responses.jsonl"
    manifest_path = output_dir / "configured_adjudicator_run_323e_response_manifest.json"
    workbook_path = output_dir / "configured_adjudicator_run_323e_request_response_workbook.xlsx"
    run_metadata_path = output_dir / "configured_adjudicator_run_323e_run_metadata.json"
    manual_template_path = output_dir / "configured_adjudicator_run_323e_manual_response_template.xlsx"
    notes_path = output_dir / "configured_adjudicator_run_323e_notes.md"
    no_apply_proof_path = output_dir / "configured_adjudicator_run_323e_no_apply_proof.json"

    sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "request_response_items": artifacts["request_response_df"],
        "manual_response_template": artifacts["manual_template_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }

    raw_rows = artifacts.get("raw_responses", [])
    if not raw_rows:
        raw_rows = artifacts.get("raw_response_placeholders", [])

    write_json(summary_path, summary)
    write_json(qa_path, artifacts["qa_json"])
    write_json(manifest_path, artifacts["response_manifest_json"])
    write_json(run_metadata_path, artifacts["run_metadata_json"])
    write_json(no_apply_proof_path, artifacts["no_apply_proof_json"])
    write_jsonl(raw_responses_path, raw_rows)
    write_excel(workbook_path, sheets, WORKBOOK_SHEET_ORDER)
    write_excel(manual_template_path, sheets, WORKBOOK_SHEET_ORDER)
    notes_path.write_text(artifacts["notes_md"], encoding="utf-8")

    output_files_written = all(
        path.exists()
        for path in [
            summary_path,
            qa_path,
            raw_responses_path,
            manifest_path,
            workbook_path,
            run_metadata_path,
            manual_template_path,
            notes_path,
            no_apply_proof_path,
        ]
    )

    qa_df = artifacts["qa_checks_df"].copy()
    qa_df = pd.concat(
        [
            qa_df,
            pd.DataFrame(
                [
                    {
                        "check_name": "output_artifact_presence",
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
    if summary["qa_fail_count"] == 0:
        summary["decision"] = (
            EXPECTED_323E_MANUAL_READY
            if args.mode == "prepare-manual"
            else "CONFIGURED_ADJUDICATOR_RUN_323E_RAW_RESPONSES_READY_FOR_323F_SCHEMA_VALIDATION"
        )
    else:
        summary["decision"] = EXPECTED_323E_NOT_READY

    sheets["summary"] = pd.DataFrame([summary]).fillna("")
    sheets["qa_checks"] = qa_df

    write_json(summary_path, summary)
    write_json(
        qa_path,
        {
            "qa_pass_count": summary["qa_pass_count"],
            "qa_warn_count": summary["qa_warn_count"],
            "qa_fail_count": summary["qa_fail_count"],
            "blocking_reasons": summary["blocking_reasons"],
            "checks": qa_df.to_dict(orient="records"),
        },
    )
    manifest_json = artifacts["response_manifest_json"]
    manifest_json["decision"] = summary["decision"]
    write_json(manifest_path, manifest_json)
    write_excel(workbook_path, sheets, WORKBOOK_SHEET_ORDER)
    write_excel(manual_template_path, sheets, WORKBOOK_SHEET_ORDER)
    notes_path.write_text(configured_adjudicator_run_report_markdown(summary), encoding="utf-8")

    print(f"configured_adjudicator_run_323e_summary_json: {summary_path}")
    print(f"configured_adjudicator_run_323e_qa_json: {qa_path}")
    print(f"configured_adjudicator_run_323e_raw_responses_jsonl: {raw_responses_path}")
    print(f"configured_adjudicator_run_323e_response_manifest_json: {manifest_path}")
    print(f"configured_adjudicator_run_323e_request_response_workbook_xlsx: {workbook_path}")
    print(f"configured_adjudicator_run_323e_run_metadata_json: {run_metadata_path}")
    print(f"configured_adjudicator_run_323e_manual_response_template_xlsx: {manual_template_path}")
    print(f"configured_adjudicator_run_323e_no_apply_proof_json: {no_apply_proof_path}")
    print(f"configured_adjudicator_run_323e_notes_md: {notes_path}")
    for key in [
        "mode",
        "request_count",
        "raw_response_count",
        "response_received_count",
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
