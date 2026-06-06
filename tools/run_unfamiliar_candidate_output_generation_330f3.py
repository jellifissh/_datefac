from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.no_apply_proof import FORMAL_SCOPE_RULES_PATH, SEMANTIC_ALIAS_ASSET_PATH  # noqa: E402
from datefac.trust.unfamiliar_candidate_output_generation_330f3 import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PREPARED_OUTPUT_DIR,
    DEFAULT_PREVIOUS_PREPARATION_DIR,
    DEFAULT_UNFAMILIAR_INPUT_DIR,
    NOT_READY_DECISION,
    build_unfamiliar_candidate_output_generation_330f3,
)
from datefac.trust.unfamiliar_candidate_output_generation_330f3_report import (  # noqa: E402
    SUMMARY_SHEET_ORDER,
    unfamiliar_candidate_output_generation_330f3_markdown,
    write_excel,
    write_json,
)


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _blocked_result(output_dir: Path, code: str, detail: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "330F3",
        "output_dir": str(output_dir),
        "prepared_output_dir": str(DEFAULT_PREPARED_OUTPUT_DIR),
        "validated_330f2_waiting_for_parser_outputs": False,
        "unfamiliar_pdf_count": 0,
        "processed_pdf_count": 0,
        "prepared_candidate_row_count": 0,
        "existing_output_match_count": 0,
        "matched_candidate_artifact_count": 0,
        "generation_export_approach_used": "C",
        "can_rerun_330f": False,
        "output_dir_for_330f": str(DEFAULT_PREPARED_OUTPUT_DIR),
        "missing_field_counts": {},
        "production_routing_modified": False,
        "official_assets_modified": False,
        "no_official_asset_modification_during_330f3": True,
        "files_written_to_official_assets": [],
        "qa_pass_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": NOT_READY_DECISION,
    }
    qa_json = {
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "checks": [{"check_name": code, "status": "FAIL", "detail": detail}],
    }
    no_apply = {
        "stage": "330F3",
        "files_read": [],
        "official_assets_before": {},
        "official_assets_after": {},
        "official_assets_written": [],
        "no_official_asset_modification_during_330f3": True,
    }
    write_json(output_dir / "unfamiliar_candidate_output_generation_330f3_summary.json", summary)
    write_json(output_dir / "unfamiliar_candidate_output_generation_330f3_qa.json", qa_json)
    write_json(output_dir / "unfamiliar_candidate_output_generation_330f3_no_apply_proof.json", no_apply)
    write_excel(
        output_dir / "unfamiliar_candidate_output_generation_330f3_summary.xlsx",
        {
            "summary": pd.DataFrame([summary]),
            "qa_summary": pd.DataFrame([{"qa_fail_count": 1, "decision": NOT_READY_DECISION}]),
            "qa_checks": pd.DataFrame(qa_json["checks"]),
            "unfamiliar_inputs": pd.DataFrame(),
            "output_matches": pd.DataFrame(),
            "matched_candidate_artifacts": pd.DataFrame(),
            "prepared_candidate_rows": pd.DataFrame(),
            "missing_field_counts": pd.DataFrame(),
            "official_asset_proof": pd.DataFrame(),
            "known_limitations": pd.DataFrame([{"candidate_path": "blocked", "status": code, "detail": detail}]),
        },
        SUMMARY_SHEET_ORDER,
    )
    (output_dir / "unfamiliar_candidate_output_generation_330f3_report.md").write_text(
        unfamiliar_candidate_output_generation_330f3_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 330F3 unfamiliar candidate output generation.")
    parser.add_argument("--unfamiliar-input-dir", default=str(DEFAULT_UNFAMILIAR_INPUT_DIR))
    parser.add_argument("--previous-preparation-dir", default=str(DEFAULT_PREVIOUS_PREPARATION_DIR))
    parser.add_argument("--prepared-output-dir", default=str(DEFAULT_PREPARED_OUTPUT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    unfamiliar_input_dir = Path(args.unfamiliar_input_dir)
    previous_preparation_dir = Path(args.previous_preparation_dir)
    prepared_output_dir = Path(args.prepared_output_dir)
    output_dir = Path(args.output_dir)

    previous_summary_path = previous_preparation_dir / "unfamiliar_output_preparation_330f2_summary.json"
    if not previous_summary_path.exists():
        summary = _blocked_result(output_dir, "BLOCKED_MISSING_330F2_SUMMARY", str(previous_summary_path))
        print(f"unfamiliar_candidate_output_generation_330f3_summary_json: {output_dir / 'unfamiliar_candidate_output_generation_330f3_summary.json'}")
        print(f"qa_fail_count: {summary['qa_fail_count']}")
        print(f"decision: {summary['decision']}")
        return 0

    artifacts = build_unfamiliar_candidate_output_generation_330f3(
        previous_preparation_summary=_read_json(previous_summary_path),
        unfamiliar_input_dir=unfamiliar_input_dir,
        output_discovery_root=PROJECT_ROOT / "output",
        prepared_output_dir=prepared_output_dir,
        output_dir=output_dir,
        alias_asset_path=SEMANTIC_ALIAS_ASSET_PATH,
        scope_asset_path=FORMAL_SCOPE_RULES_PATH,
        files_read=[
            str(previous_summary_path),
            str(unfamiliar_input_dir),
            str(PROJECT_ROOT / "output"),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "unfamiliar_candidate_output_generation_330f3_summary.json"
    qa_json = output_dir / "unfamiliar_candidate_output_generation_330f3_qa.json"
    no_apply_json = output_dir / "unfamiliar_candidate_output_generation_330f3_no_apply_proof.json"
    manifest_json = output_dir / "unfamiliar_candidate_output_generation_330f3_manifest.json"
    summary_xlsx = output_dir / "unfamiliar_candidate_output_generation_330f3_summary.xlsx"
    report_md = output_dir / "unfamiliar_candidate_output_generation_330f3_report.md"

    write_json(summary_json, artifacts["summary"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_apply_json, artifacts["no_apply_proof_json"])
    write_json(manifest_json, artifacts["prepared_manifest_json"])
    write_excel(
        summary_xlsx,
        {
            "summary": artifacts["summary_df"],
            "qa_summary": artifacts["qa_summary_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "unfamiliar_inputs": artifacts["unfamiliar_inputs_df"],
            "output_matches": artifacts["output_matches_df"],
            "matched_candidate_artifacts": artifacts["matched_candidate_artifacts_df"],
            "prepared_candidate_rows": artifacts["prepared_candidate_rows_df"],
            "missing_field_counts": artifacts["missing_field_counts_df"],
            "official_asset_proof": artifacts["official_asset_proof_df"],
            "known_limitations": artifacts["known_limitations_df"],
        },
        SUMMARY_SHEET_ORDER,
    )
    report_md.write_text(unfamiliar_candidate_output_generation_330f3_markdown(artifacts["summary"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"unfamiliar_candidate_output_generation_330f3_summary_json: {summary_json}")
    print(f"unfamiliar_candidate_output_generation_330f3_qa_json: {qa_json}")
    print(f"unfamiliar_candidate_output_generation_330f3_no_apply_proof_json: {no_apply_json}")
    print(f"unfamiliar_candidate_output_generation_330f3_manifest_json: {manifest_json}")
    print(f"unfamiliar_candidate_output_generation_330f3_summary_xlsx: {summary_xlsx}")
    print(f"unfamiliar_candidate_output_generation_330f3_report_md: {report_md}")
    for key in [
        "validated_330f2_waiting_for_parser_outputs",
        "unfamiliar_pdf_count",
        "processed_pdf_count",
        "prepared_candidate_row_count",
        "existing_output_match_count",
        "matched_candidate_artifact_count",
        "generation_export_approach_used",
        "can_rerun_330f",
        "no_official_asset_modification_during_330f3",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
