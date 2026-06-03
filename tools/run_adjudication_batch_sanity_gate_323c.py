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

from datefac.semantic.adjudication_batch_sanity_gate import (
    DEFAULT_BATCH_PREP_DIR,
    DEFAULT_CANDIDATE_TEXT_REPAIR_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PATCH_APPLICATION_DIR,
    EXPECTED_323C_NOT_READY_DECISION,
    build_adjudication_batch_sanity_gate_323c,
    load_adjudication_batch_sanity_gate_323c_inputs,
)
from datefac.semantic.adjudication_batch_sanity_gate_report import (
    GATED_BATCH_SHEET_ORDER,
    SIMPLE_ITEM_SHEET_ORDER,
    adjudication_batch_sanity_gate_323c_notes_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "323C",
        "output_dir": str(output_dir),
        "input_batch_count": 0,
        "input_alias_batch_count": 0,
        "input_scope_batch_count": 0,
        "routing_bucket_counts": {},
        "suspicious_alias_count": 0,
        "send_to_adjudicator_count": 0,
        "human_spot_check_count": 0,
        "holdout_category_mismatch_count": 0,
        "holdout_ambiguous_count": 0,
        "holdout_already_official_count": 0,
        "holdout_invalid_text_count": 0,
        "highest_priority_gated_examples": [],
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_323C_NOT_READY_DECISION,
    }
    qa_json = {
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}],
    }
    gated_batch_json = {"stage": "323C", "decision": summary["decision"], "batch_items": []}

    workbook_sheets = {
        "summary": pd.DataFrame([summary]),
        "gated_batch": pd.DataFrame(),
        "send_to_adjudicator": pd.DataFrame(),
        "human_spot_check": pd.DataFrame(),
        "holdouts": pd.DataFrame(),
        "qa_summary": pd.DataFrame(
            [
                {
                    "qa_pass_count": 0,
                    "qa_warn_count": 0,
                    "qa_fail_count": 1,
                    "blocking_reasons": code,
                    "decision": summary["decision"],
                }
            ]
        ),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
        "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": "Required input directory is missing."}]),
    }
    simple_sheets = {
        "summary": pd.DataFrame([summary]),
        "items": pd.DataFrame(),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
    }

    write_json(output_dir / "adjudication_batch_sanity_gate_323c_summary.json", summary)
    write_json(output_dir / "adjudication_batch_sanity_gate_323c_qa.json", qa_json)
    write_json(output_dir / "adjudication_batch_sanity_gate_323c_gated_batch.json", gated_batch_json)
    write_excel(
        output_dir / "adjudication_batch_sanity_gate_323c_gated_batch.xlsx",
        workbook_sheets,
        GATED_BATCH_SHEET_ORDER,
    )
    write_excel(
        output_dir / "adjudication_batch_sanity_gate_323c_human_spot_check.xlsx",
        simple_sheets,
        SIMPLE_ITEM_SHEET_ORDER,
    )
    write_excel(
        output_dir / "adjudication_batch_sanity_gate_323c_send_to_adjudicator.xlsx",
        simple_sheets,
        SIMPLE_ITEM_SHEET_ORDER,
    )
    write_excel(
        output_dir / "adjudication_batch_sanity_gate_323c_holdouts.xlsx",
        simple_sheets,
        SIMPLE_ITEM_SHEET_ORDER,
    )
    (output_dir / "adjudication_batch_sanity_gate_323c_notes.md").write_text(
        adjudication_batch_sanity_gate_323c_notes_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 323C adjudication batch sanity gate.")
    parser.add_argument("--batch-prep-dir", default=str(DEFAULT_BATCH_PREP_DIR))
    parser.add_argument("--candidate-text-repair-dir", default=str(DEFAULT_CANDIDATE_TEXT_REPAIR_DIR))
    parser.add_argument("--patch-application-dir", default=str(DEFAULT_PATCH_APPLICATION_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    batch_prep_dir = Path(args.batch_prep_dir)
    candidate_text_repair_dir = Path(args.candidate_text_repair_dir)
    patch_application_dir = Path(args.patch_application_dir)
    output_dir = Path(args.output_dir)

    required_dirs = [
        (batch_prep_dir, "BLOCKED_MISSING_323AB_BATCH_PREP_DIR"),
        (candidate_text_repair_dir, "BLOCKED_MISSING_323AR_DIR"),
        (patch_application_dir, "BLOCKED_MISSING_322N_PATCH_APPLICATION_DIR"),
    ]
    for path, code in required_dirs:
        if not path.exists():
            _blocked_result(output_dir, code)
            print(f"adjudication_batch_sanity_gate_323c_summary_json: {output_dir / 'adjudication_batch_sanity_gate_323c_summary.json'}")
            return 0

    inputs = load_adjudication_batch_sanity_gate_323c_inputs(
        batch_prep_dir=batch_prep_dir,
        candidate_text_repair_dir=candidate_text_repair_dir,
        patch_application_dir=patch_application_dir,
    )
    artifacts = build_adjudication_batch_sanity_gate_323c(
        batch_prep_summary=inputs["batch_prep_summary"],
        batch_prep_qa=inputs["batch_prep_qa"],
        batch_items=inputs["batch_items"],
        candidate_text_repair_summary=inputs["candidate_text_repair_summary"],
        patch_application_log_df=inputs["patch_application_log_df"],
    )

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = output_dir / "adjudication_batch_sanity_gate_323c_summary.json"
    qa_path = output_dir / "adjudication_batch_sanity_gate_323c_qa.json"
    gated_batch_json_path = output_dir / "adjudication_batch_sanity_gate_323c_gated_batch.json"
    gated_batch_xlsx_path = output_dir / "adjudication_batch_sanity_gate_323c_gated_batch.xlsx"
    human_spot_check_xlsx_path = output_dir / "adjudication_batch_sanity_gate_323c_human_spot_check.xlsx"
    send_to_adjudicator_xlsx_path = output_dir / "adjudication_batch_sanity_gate_323c_send_to_adjudicator.xlsx"
    holdouts_xlsx_path = output_dir / "adjudication_batch_sanity_gate_323c_holdouts.xlsx"
    notes_path = output_dir / "adjudication_batch_sanity_gate_323c_notes.md"

    workbook_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "gated_batch": artifacts["gated_batch_df"],
        "send_to_adjudicator": artifacts["send_to_adjudicator_df"],
        "human_spot_check": artifacts["human_spot_check_df"],
        "holdouts": artifacts["holdouts_df"],
        "qa_summary": artifacts["qa_summary_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }
    human_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "items": artifacts["human_spot_check_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }
    send_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "items": artifacts["send_to_adjudicator_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }
    holdout_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "items": artifacts["holdouts_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }

    write_json(summary_path, summary)
    write_json(qa_path, artifacts["qa_json"])
    write_json(gated_batch_json_path, artifacts["gated_batch_json"])
    write_excel(gated_batch_xlsx_path, workbook_sheets, GATED_BATCH_SHEET_ORDER)
    write_excel(human_spot_check_xlsx_path, human_sheets, SIMPLE_ITEM_SHEET_ORDER)
    write_excel(send_to_adjudicator_xlsx_path, send_sheets, SIMPLE_ITEM_SHEET_ORDER)
    write_excel(holdouts_xlsx_path, holdout_sheets, SIMPLE_ITEM_SHEET_ORDER)
    notes_path.write_text(adjudication_batch_sanity_gate_323c_notes_markdown(summary), encoding="utf-8")

    output_files_written = all(
        path.exists()
        for path in [
            summary_path,
            qa_path,
            gated_batch_json_path,
            gated_batch_xlsx_path,
            human_spot_check_xlsx_path,
            send_to_adjudicator_xlsx_path,
            holdouts_xlsx_path,
            notes_path,
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
    summary["decision"] = (
        "ADJUDICATION_BATCH_SANITY_GATE_323C_READY_FOR_HUMAN_SPOT_CHECK_OR_SAFE_ADJUDICATOR_SUBSET"
        if summary["qa_fail_count"] == 0
        else EXPECTED_323C_NOT_READY_DECISION
    )

    workbook_sheets["summary"] = pd.DataFrame([summary]).fillna("")
    workbook_sheets["qa_summary"] = pd.DataFrame(
        [
            {
                "qa_pass_count": summary["qa_pass_count"],
                "qa_warn_count": summary["qa_warn_count"],
                "qa_fail_count": summary["qa_fail_count"],
                "blocking_reasons": " | ".join(summary["blocking_reasons"]),
                "decision": summary["decision"],
            }
        ]
    ).fillna("")
    workbook_sheets["qa_checks"] = qa_df
    human_sheets["summary"] = pd.DataFrame([summary]).fillna("")
    human_sheets["qa_checks"] = qa_df
    send_sheets["summary"] = pd.DataFrame([summary]).fillna("")
    send_sheets["qa_checks"] = qa_df
    holdout_sheets["summary"] = pd.DataFrame([summary]).fillna("")
    holdout_sheets["qa_checks"] = qa_df

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
    write_json(
        gated_batch_json_path,
        {
            "stage": "323C",
            "decision": summary["decision"],
            "batch_items": artifacts["gated_batch_json"].get("batch_items", []),
        },
    )
    write_excel(gated_batch_xlsx_path, workbook_sheets, GATED_BATCH_SHEET_ORDER)
    write_excel(human_spot_check_xlsx_path, human_sheets, SIMPLE_ITEM_SHEET_ORDER)
    write_excel(send_to_adjudicator_xlsx_path, send_sheets, SIMPLE_ITEM_SHEET_ORDER)
    write_excel(holdouts_xlsx_path, holdout_sheets, SIMPLE_ITEM_SHEET_ORDER)
    notes_path.write_text(adjudication_batch_sanity_gate_323c_notes_markdown(summary), encoding="utf-8")

    print(f"adjudication_batch_sanity_gate_323c_summary_json: {summary_path}")
    print(f"adjudication_batch_sanity_gate_323c_qa_json: {qa_path}")
    print(f"adjudication_batch_sanity_gate_323c_gated_batch_json: {gated_batch_json_path}")
    print(f"adjudication_batch_sanity_gate_323c_gated_batch_xlsx: {gated_batch_xlsx_path}")
    print(f"adjudication_batch_sanity_gate_323c_human_spot_check_xlsx: {human_spot_check_xlsx_path}")
    print(f"adjudication_batch_sanity_gate_323c_send_to_adjudicator_xlsx: {send_to_adjudicator_xlsx_path}")
    print(f"adjudication_batch_sanity_gate_323c_holdouts_xlsx: {holdouts_xlsx_path}")
    print(f"adjudication_batch_sanity_gate_323c_notes_md: {notes_path}")
    for key in [
        "input_batch_count",
        "suspicious_alias_count",
        "send_to_adjudicator_count",
        "human_spot_check_count",
        "holdout_category_mismatch_count",
        "holdout_ambiguous_count",
        "holdout_already_official_count",
        "holdout_invalid_text_count",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
