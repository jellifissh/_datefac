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

from datefac.semantic.scope_noise_adjudicator_response_collection_324d import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REQUEST_DIR,
    EXPECTED_324D_MANUAL_READY,
    EXPECTED_324D_NOT_READY,
    EXPECTED_324D_RAW_READY,
    build_scope_noise_adjudicator_response_collection_324d_collect_manual,
    build_scope_noise_adjudicator_response_collection_324d_prepare_manual,
    load_scope_noise_adjudicator_response_collection_324d_inputs,
)
from datefac.semantic.scope_noise_adjudicator_response_collection_324d_report import (  # noqa: E402
    WORKBOOK_SHEET_ORDER,
    scope_noise_adjudicator_response_collection_324d_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def _blocked_result(output_dir: Path, mode: str, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "324D",
        "mode": mode,
        "output_dir": str(output_dir),
        "request_count": 0,
        "raw_response_count": 0,
        "response_received_count": 0,
        "llm_or_adjudicator_called": False,
        "collect_manual_mode_implemented": True,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_324D_NOT_READY,
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
    write_json(output_dir / "scope_noise_adjudicator_response_collection_324d_summary.json", summary)
    write_json(output_dir / "scope_noise_adjudicator_response_collection_324d_qa.json", qa_json)
    write_json(output_dir / "scope_noise_adjudicator_response_collection_324d_response_manifest.json", {"raw_response_count": 0})
    write_json(output_dir / "scope_noise_adjudicator_response_collection_324d_run_metadata.json", {"mode": mode, "decision": "blocked_input"})
    write_json(output_dir / "scope_noise_adjudicator_response_collection_324d_no_apply_proof.json", {"decision": "blocked_input"})
    write_jsonl(output_dir / "scope_noise_adjudicator_response_collection_324d_raw_responses.jsonl", [])
    write_excel(
        output_dir / "scope_noise_adjudicator_response_collection_324d_request_response_workbook.xlsx",
        sheets,
    )
    write_excel(
        output_dir / "scope_noise_adjudicator_response_collection_324d_manual_response_template.xlsx",
        sheets,
    )
    (output_dir / "scope_noise_adjudicator_response_collection_324d_notes.md").write_text(
        scope_noise_adjudicator_response_collection_324d_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 324D scope-noise adjudicator raw response collection.")
    parser.add_argument("--mode", choices=["prepare-manual", "collect-manual"], default="prepare-manual")
    parser.add_argument("--request-dir", default=str(DEFAULT_REQUEST_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--manual-response-workbook", default="")
    args = parser.parse_args()

    request_dir = Path(args.request_dir)
    output_dir = Path(args.output_dir)
    manual_response_workbook = Path(args.manual_response_workbook) if args.manual_response_workbook else (
        output_dir / "scope_noise_adjudicator_response_collection_324d_manual_response_template.xlsx"
    )

    required_paths = [
        request_dir / "scope_noise_safe_adjudicator_request_324c_summary.json",
        request_dir / "scope_noise_safe_adjudicator_request_324c_qa.json",
        request_dir / "scope_noise_safe_adjudicator_request_324c_request_package.json",
    ]
    if not all(path.exists() for path in required_paths):
        _blocked_result(output_dir, args.mode, "BLOCKED_MISSING_324C_REQUEST_ARTIFACTS")
        print(
            "scope_noise_adjudicator_response_collection_324d_summary_json: "
            f"{output_dir / 'scope_noise_adjudicator_response_collection_324d_summary.json'}"
        )
        return 0

    if args.mode == "collect-manual" and not manual_response_workbook.exists():
        _blocked_result(output_dir, args.mode, "BLOCKED_MISSING_MANUAL_RESPONSE_WORKBOOK")
        print(
            "scope_noise_adjudicator_response_collection_324d_summary_json: "
            f"{output_dir / 'scope_noise_adjudicator_response_collection_324d_summary.json'}"
        )
        return 0

    inputs = load_scope_noise_adjudicator_response_collection_324d_inputs(request_dir=request_dir)
    if args.mode == "prepare-manual":
        artifacts = build_scope_noise_adjudicator_response_collection_324d_prepare_manual(
            inputs=inputs,
            mode=args.mode,
            request_dir=request_dir,
        )
    else:
        artifacts = build_scope_noise_adjudicator_response_collection_324d_collect_manual(
            inputs=inputs,
            mode=args.mode,
            request_dir=request_dir,
            manual_response_workbook=manual_response_workbook,
        )

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = output_dir / "scope_noise_adjudicator_response_collection_324d_summary.json"
    qa_path = output_dir / "scope_noise_adjudicator_response_collection_324d_qa.json"
    raw_responses_path = output_dir / "scope_noise_adjudicator_response_collection_324d_raw_responses.jsonl"
    manifest_path = output_dir / "scope_noise_adjudicator_response_collection_324d_response_manifest.json"
    workbook_path = output_dir / "scope_noise_adjudicator_response_collection_324d_request_response_workbook.xlsx"
    run_metadata_path = output_dir / "scope_noise_adjudicator_response_collection_324d_run_metadata.json"
    manual_template_path = output_dir / "scope_noise_adjudicator_response_collection_324d_manual_response_template.xlsx"
    notes_path = output_dir / "scope_noise_adjudicator_response_collection_324d_notes.md"
    no_apply_proof_path = output_dir / "scope_noise_adjudicator_response_collection_324d_no_apply_proof.json"

    sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "request_response_items": artifacts["request_response_df"],
        "manual_response_template": artifacts["manual_template_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }

    write_json(summary_path, summary)
    write_json(qa_path, artifacts["qa_json"])
    write_json(manifest_path, artifacts["response_manifest_json"])
    write_json(run_metadata_path, artifacts["run_metadata_json"])
    write_json(no_apply_proof_path, artifacts["no_apply_proof_json"])
    write_jsonl(raw_responses_path, artifacts["raw_responses"])
    write_excel(workbook_path, sheets)
    write_excel(manual_template_path, sheets)
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
        summary["decision"] = EXPECTED_324D_MANUAL_READY if args.mode == "prepare-manual" else EXPECTED_324D_RAW_READY
    else:
        summary["decision"] = EXPECTED_324D_NOT_READY

    manifest_json = artifacts["response_manifest_json"]
    manifest_json["decision"] = summary["decision"]
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
    write_json(manifest_path, manifest_json)
    write_excel(workbook_path, sheets)
    write_excel(manual_template_path, sheets)
    notes_path.write_text(scope_noise_adjudicator_response_collection_324d_markdown(summary), encoding="utf-8")

    print(f"scope_noise_adjudicator_response_collection_324d_summary_json: {summary_path}")
    print(f"scope_noise_adjudicator_response_collection_324d_qa_json: {qa_path}")
    print(f"scope_noise_adjudicator_response_collection_324d_raw_responses_jsonl: {raw_responses_path}")
    print(f"scope_noise_adjudicator_response_collection_324d_response_manifest_json: {manifest_path}")
    print(f"scope_noise_adjudicator_response_collection_324d_request_response_workbook_xlsx: {workbook_path}")
    print(f"scope_noise_adjudicator_response_collection_324d_run_metadata_json: {run_metadata_path}")
    print(f"scope_noise_adjudicator_response_collection_324d_manual_response_template_xlsx: {manual_template_path}")
    print(f"scope_noise_adjudicator_response_collection_324d_no_apply_proof_json: {no_apply_proof_path}")
    print(f"scope_noise_adjudicator_response_collection_324d_notes_md: {notes_path}")
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
